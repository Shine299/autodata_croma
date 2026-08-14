"""Tests unitarios para B-08 (Adapter SUTRAN) y B-09 (Adapter Callao + Merge Infractions)."""

import json
from pathlib import Path

import pytest

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.callao import map_callao_infractions, merge_infractions
from app.integrations.croma.sources.sutran import map_sutran_infractions
from app.schemas.vehicle import Infractions

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sutran_clean_sample():
    return json.loads((FIXTURES_DIR / "sutran_sample.json").read_text())


@pytest.fixture
def callao_clean_sample():
    return json.loads((FIXTURES_DIR / "callao_sample.json").read_text())


def test_map_sutran_clean(sutran_clean_sample):
    """Prueba mapeo de SUTRAN sin infracciones pendientes."""
    res = SourceResult(source="SUTRAN", status="ok", data=sutran_clean_sample)
    infractions = map_sutran_infractions(res)

    assert isinstance(infractions, Infractions)
    assert infractions.status == "ok"
    assert infractions.has_infractions is False
    assert infractions.count == 0
    assert infractions.total == 0.0
    assert infractions.severe_count == 0
    assert len(infractions.items) == 0


def test_map_sutran_with_infractions():
    """Prueba SUTRAN con infracciones graves y muy graves."""
    sutran_data = {
        "found": True,
        "plate": "ABC-123",
        "has_infractions": True,
        "count": 2,
        "currency": "PEN",
        "total": 1250.50,
        "infractions": [
            {
                "document_number": "P-100201",
                "document_type": "PAPELETA",
                "document_date": "2025-05-10",
                "infraction_code": "M01",
                "classification": "Muy Grave",
                "amount": 1000.0,
            },
            {
                "document_number": "P-100202",
                "document_type": "PAPELETA",
                "document_date": "2025-06-15",
                "infraction_code": "G04",
                "classification": "Grave",
                "amount": 250.50,
            },
        ],
    }
    infractions = map_sutran_infractions(sutran_data)

    assert infractions.has_infractions is True
    assert infractions.count == 2
    assert infractions.total == 1250.50
    assert infractions.severe_count == 1
    assert infractions.items[0].source == "SUTRAN"
    assert infractions.items[0].classification == "Muy Grave"


def test_map_callao_and_merge():
    """Prueba consolidación de SUTRAN + Callao con asignación correcta de source='CALLAO'."""
    sutran_data = {
        "found": True,
        "infractions": [
            {
                "document_number": "SUTRAN-01",
                "infraction_code": "G01",
                "classification": "Grave",
                "amount": 400.0,
            }
        ],
        "total": 400.0,
    }

    callao_data = {
        "found": True,
        "papeletas": [
            {
                "document_number": "CALLAO-99",
                "infraction_code": "M02",
                "classification": "Muy Grave",
                "amount": 600.0,
            }
        ],
        "total": 600.0,
    }

    merged = merge_infractions(sutran_data, callao_data)

    assert isinstance(merged, Infractions)
    assert merged.status == "ok"
    assert merged.has_infractions is True
    assert merged.count == 2
    assert merged.total == 1000.0
    assert merged.severe_count == 1

    # Verificar que los sources queden correctamente identificados
    sources = [item.source for item in merged.items]
    assert "SUTRAN" in sources
    assert "CALLAO" in sources
    assert merged.items[1].source == "CALLAO"


def test_merge_infractions_when_callao_fails():
    """Prueba que si Callao falla, no tumba las infracciones de SUTRAN."""
    sutran_ok = {
        "found": True,
        "infractions": [
            {
                "document_number": "SUTRAN-01",
                "infraction_code": "M01",
                "classification": "Muy Grave",
                "amount": 500.0,
            }
        ],
        "total": 500.0,
    }
    callao_err = SourceResult(source="CALLAO", status="error", error="service_unavailable")

    merged = merge_infractions(sutran_ok, callao_err)
    assert merged.status == "ok"
    assert merged.has_infractions is True
    assert merged.count == 1
    assert merged.total == 500.0
    assert merged.severe_count == 1
