"""Mejoras del asistente de compra: parsing robusto y recomendación honesta."""

from app.bot.parsers import format_plate_display, parse_plate, parse_price
from app.bot.formatters import (
    confidence_level,
    format_detail,
    format_verdict,
    purchase_recommendation,
)
from app.bot.handlers import _ASK_PLATE, next_state
from app.bot.states import State
from app.schemas.conversation import Extracted


# --- No re-verificar cuando el usuario solo saluda (bug reportado) ----------

def test_greeting_while_done_does_not_reverify():
    # Chat que quedó en DONE de una consulta previa. El usuario escribe "Hola".
    new_state, ctx, reply = next_state(State.DONE, Extracted(), {"plate": "COH099"}, text="Hola")
    # NO debe quedarse en DONE (si no, on_text re-dispara la verificación en vano).
    assert new_state is State.IDLE
    assert reply == _ASK_PLATE


def test_awaiting_price_keeps_waiting_on_junk():
    new_state, ctx, reply = next_state(
        State.AWAITING_PRICE, Extracted(), {"plate": "COH099"}, text="ehh no sé"
    )
    assert new_state is State.AWAITING_PRICE
    assert reply != _ASK_PLATE  # sigue pidiendo el precio, no la placa


# --- Parsing de placa (no confundir formatos ni re-preguntar) --------------

def test_plate_accepts_space_dash_and_none():
    assert parse_plate("COH-099") == "COH099"
    assert parse_plate("COH 099") == "COH099"
    assert parse_plate("coh099") == "COH099"


def test_plate_display_adds_dash():
    assert format_plate_display("COH099") == "COH-099"
    assert format_plate_display("1234AB") == "1234-AB"
    assert format_plate_display("AB1234") == "AB-1234"


# --- Parsing de precio (29k, S/29.000, 29 mil) -----------------------------

def test_price_formats():
    assert parse_price("29 mil") == 29000
    assert parse_price("29k") == 29000
    assert parse_price("S/ 29,000") == 29000
    assert parse_price("S/29.000") == 29000
    assert parse_price("29000") == 29000


# --- Recomendación determinista + confianza --------------------------------

def _data(verdict, verified, total, capture_status="ok"):
    return {
        "verdict": verdict,
        "confidence": {"verifiedSources": verified, "totalSources": total},
        "vehicle": {"captureOrder": {"status": capture_status, "hasCaptureOrder": verdict == "STOP"}},
    }


def test_recommendation_stop_is_no_comprar():
    emoji, label, _ = purchase_recommendation(_data("STOP", 6, 6))
    assert (emoji, label) == ("🔴", "NO COMPRAR")


def test_recommendation_go_all_verified_is_comprar():
    emoji, label, _ = purchase_recommendation(_data("GO", 6, 6))
    assert (emoji, label) == ("🟢", "COMPRAR")


def test_recommendation_insufficient_when_two_sources_down():
    emoji, label, _ = purchase_recommendation(_data("GO", 4, 6))
    assert (emoji, label) == ("⚪", "INFORMACIÓN INSUFICIENTE")


def test_recommendation_insufficient_when_capture_source_failed():
    # Aunque solo falle 1 fuente, si es la de orden de captura → no se asume limpio.
    emoji, label, _ = purchase_recommendation(_data("GO", 5, 6, capture_status="error"))
    assert (emoji, label) == ("⚪", "INFORMACIÓN INSUFICIENTE")


def test_confidence_low_when_source_unavailable():
    assert confidence_level(_data("GO", 4, 6))[1] == "BAJA"
    assert confidence_level(_data("GO", 6, 6))[1] == "ALTA"


# --- Reporte honesto -------------------------------------------------------

def test_report_marks_no_disponible_and_never_claims_clean_when_source_fails():
    data = {
        "verdict": "GO",
        "plate": "COH099",
        "headline": "Todo en orden",
        "flags": [],
        "confidence": {"verifiedSources": 5, "totalSources": 6},
        "vehicle": {
            "insurance": {"status": "ok", "hasActiveSoat": True, "accidentCount": 0},
            "infractions": {"status": "ok", "total": 0, "count": 0, "severeCount": 0},
            "taxDebt": {"status": "ok", "total": 0},
            "captureOrder": {"status": "error"},  # la fuente crítica falló
        },
        "appraisal": {
            "askingPrice": 29000,
            "fairPrice": 29000,
            "deductions": [],
        },
    }
    text = format_verdict(data)
    assert "NO DISPONIBLE" in text
    assert "COH-099" in text
    # Fuente crítica caída → información insuficiente, jamás afirma que esté verificado.
    assert "INFORMACIÓN INSUFICIENTE" in text
    assert "no verificado" in text.lower()  # la orden de captura queda como pendiente
    assert confidence_level(data)[1] == "BAJA"
    # Muestra el análisis de precio con el objetivo.
    assert "ANÁLISIS DEL PRECIO" in text
    assert "29,000" in text


def test_format_detail_shows_items_and_sources():
    data = {
        "verificationId": "abc-123",
        "plate": "GHI789",
        "vehicle": {
            "insurance": {"status": "ok", "hasActiveSoat": False, "accidentCount": 0, "company": "Rimac"},
            "infractions": {
                "status": "ok", "total": 2340, "count": 3, "severeCount": 1,
                "items": [{"infractionCode": "M.1", "classification": "Muy Grave", "source": "SUTRAN"}],
            },
            "taxDebt": {"status": "ok", "total": 1850, "items": [{"concept": "Impuesto", "period": "2023", "amount": 950}]},
            "captureOrder": {"status": "ok", "hasCaptureOrder": False},
            "sourcesSummary": [{"source": "sutran", "status": "ok", "latencyMs": 120}],
        },
    }
    text = format_detail(data)
    assert "GHI-789" in text
    assert "M.1" in text                 # papeleta ítem por ítem
    assert "Impuesto" in text            # deuda desglosada
    assert "SUTRAN (papeletas)" in text  # estado de la fuente
    assert "abc-123" in text             # id de consulta
