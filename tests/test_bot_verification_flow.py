"""D-04 — Tests del flujo bot → POST /verifications.

DoD verificado: un fallo de la API (502/timeout) produce un mensaje amable y NO un
crash del handler. También se cubre el happy path: se rinde `format_verdict` (D-06) y
se cuelgan los botones con `verdict_keyboard` (D-07).

Se prueba `_deliver_verdict` directamente (no toca la base) mockeando el cliente HTTP.
"""

import json
from pathlib import Path

import pytest
from telegram import InlineKeyboardMarkup

from app.bot import handlers
from app.bot.api_client import VerificationApiError

FIXTURES = Path(__file__).parent / "fixtures"


class _FakeMessage:
    """Captura las llamadas a reply_text para inspeccionarlas en el test."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def reply_text(self, text, parse_mode=None, reply_markup=None):
        self.calls.append(
            {"text": text, "parse_mode": parse_mode, "reply_markup": reply_markup}
        )


@pytest.mark.asyncio
async def test_api_502_shows_friendly_message_no_crash(monkeypatch):
    """[DoD D-04] Un 502 → mensaje amable, sin propagar excepción."""

    async def _boom(*args, **kwargs):
        raise VerificationApiError("boom", status_code=502)

    monkeypatch.setattr(handlers, "create_verification", _boom)

    msg = _FakeMessage()
    # No debe lanzar.
    await handlers._deliver_verdict(msg, {"plate": "ABC123", "asking_price": 32000})

    assert len(msg.calls) == 1
    assert msg.calls[0]["text"] == handlers._API_ERROR
    assert msg.calls[0]["reply_markup"] is None


@pytest.mark.asyncio
async def test_happy_path_renders_verdict_with_keyboard(monkeypatch):
    data = json.loads((FIXTURES / "verification_go.json").read_text(encoding="utf-8"))

    async def _ok(*args, **kwargs):
        return data

    monkeypatch.setattr(handlers, "create_verification", _ok)

    msg = _FakeMessage()
    await handlers._deliver_verdict(msg, {"plate": "ABC123", "asking_price": 32000})

    assert len(msg.calls) == 1
    call = msg.calls[0]
    # El veredicto formateado (D-06): semáforo verde + placa (mostrada con guion).
    assert "🟢" in call["text"]
    assert "ABC-123" in call["text"]
    # Los 4 botones (D-07) cuelgan del mensaje con el verificationId correcto.
    assert isinstance(call["reply_markup"], InlineKeyboardMarkup)
    assert "ver_go_0001" in call["reply_markup"].inline_keyboard[0][0].callback_data
