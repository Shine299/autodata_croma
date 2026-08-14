"""Tests unitarios para B-10 (SAT Lima Cuenta) y B-11 (SAT Lima Capturas)."""

import json
from pathlib import Path

import pytest

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sat_captures import map_sat_capture_order
from app.integrations.croma.sources.sat_debt import map_sat_tax_debt
from app.schemas.vehicle import CaptureOrder, TaxDebt

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sat_debt_clean():
    return json.loads((FIXTURES_DIR / "sat_lima_sample.json").read_text())


@pytest.fixture
def sat_captures_clean():
    return json.loads((FIXTURES_DIR / "sat_capturas_sample.json").read_text())


# --- Tests B-10: SAT Lima Tax Debt ---------------------------------------


def test_map_sat_debt_clean(sat_debt_clean):
    """Prueba vehículo sin deuda tributaria/vehicular."""
    res = SourceResult(source="SAT_LIMA", status="ok", data=sat_debt_clean)
    debt = map_sat_tax_debt(res)

    assert isinstance(debt, TaxDebt)
    assert debt.status == "ok"
    assert debt.has_debt is False
    assert debt.total == 0.0
    assert len(debt.items) == 0
    assert debt.source == "SAT_LIMA"


def test_map_sat_debt_with_items():
    """Prueba vehículo con deudas de impuesto vehicular y arbitrios."""
    raw_data = {
        "found": True,
        "plate": "ABC-123",
        "has_debt": True,
        "currency": "PEN",
        "total": 850.50,
        "items": [
            {"concept": "Impuesto Vehicular Cuota 1", "period": "2025", "amount": 450.00},
            {"concept": "Impuesto Vehicular Cuota 2", "period": "2025", "amount": 400.50},
        ],
    }
    debt = map_sat_tax_debt(raw_data)

    assert debt.has_debt is True
    assert debt.total == 850.50
    assert len(debt.items) == 2
    assert debt.items[0].concept == "Impuesto Vehicular Cuota 1"
    assert debt.items[0].amount == 450.00


def test_map_sat_debt_error_graceful():
    """Prueba degradación si SAT cuenta falla."""
    err = SourceResult(source="SAT_LIMA", status="error", error="timeout")
    debt = map_sat_tax_debt(err)

    assert debt.status == "error"
    assert debt.has_debt is False
    assert debt.total == 0.0


# --- Tests B-11: SAT Lima Capturas ---------------------------------------


def test_map_sat_captures_clean(sat_captures_clean):
    """Prueba vehículo sin orden de captura."""
    res = SourceResult(source="SAT_LIMA", status="ok", data=sat_captures_clean)
    capture = map_sat_capture_order(res)

    assert isinstance(capture, CaptureOrder)
    assert capture.status == "ok"
    assert capture.has_capture_order is False
    assert capture.issued_at is None
    assert capture.reason is None
    assert capture.source == "SAT_LIMA"


def test_map_sat_captures_active():
    """Prueba vehículo con orden de captura vigente e internamiento."""
    raw_data = {
        "found": True,
        "plate": "ABC-123",
        "has_capture_order": True,
        "issued_at": "2025-11-20",
        "reason": "Ejecución coactiva por acumulación de papeletas de tránsito",
    }
    capture = map_sat_capture_order(raw_data)

    assert capture.has_capture_order is True
    assert capture.issued_at == "2025-11-20"
    assert "coactiva" in capture.reason.lower()
    assert capture.source == "SAT_LIMA"


def test_map_sat_captures_error_graceful():
    """Prueba degradación si SAT capturas falla."""
    err = SourceResult(source="SAT_LIMA", status="error", error="502_upstream_error")
    capture = map_sat_capture_order(err)

    assert capture.status == "error"
    assert capture.has_capture_order is False
