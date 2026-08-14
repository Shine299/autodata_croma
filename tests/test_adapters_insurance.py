"""Tests unitarios para B-06 (Adapter SBS) y B-07 (Adapter APESEG + Merge SBS)."""

import json
from pathlib import Path

import pytest

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.apeseg import map_apeseg_soat, merge_insurance_sources
from app.integrations.croma.sources.sbs import map_sbs_soat
from app.schemas.vehicle import Insurance

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sbs_sample():
    return json.loads((FIXTURES_DIR / "sbs_soat_sample.json").read_text())


@pytest.fixture
def apeseg_sample():
    return json.loads((FIXTURES_DIR / "apeseg_soat_sample.json").read_text())


def test_map_sbs_sample(sbs_sample):
    """Prueba mapeo de fixture real de SBS."""
    res = SourceResult(source="SBS", status="ok", data=sbs_sample)
    insurance = map_sbs_soat(res)

    assert isinstance(insurance, Insurance)
    assert insurance.status == "ok"
    assert insurance.source == "SBS"
    assert insurance.accident_count == 0
    assert insurance.has_active_soat is False


def test_map_sbs_with_accidents():
    """Prueba SBS cuando registra siniestros e historial de pólizas."""
    sbs_data = {
        "found": True,
        "plate": "ABC-123",
        "accident_count": 2,
        "data_through": "2026-06-30",
        "count": 3,
        "policies": [{"company": "Rimac", "start_date": "2024-01-01"}],
    }
    insurance = map_sbs_soat(sbs_data)
    assert insurance.accident_count == 2
    assert insurance.data_through == "2026-06-30"
    assert insurance.policy_count == 3


def test_map_apeseg_sample(apeseg_sample):
    """Prueba mapeo de fixture real de APESEG."""
    res = SourceResult(source="APESEG", status="ok", data=apeseg_sample)
    apeseg = map_apeseg_soat(res)

    assert apeseg["status"] == "ok"
    assert apeseg["has_active_soat"] is True
    assert apeseg["company"] == "La Positiva"
    assert apeseg["policy_number"] == "000142242589000000000000"
    assert apeseg["start_date"] == "2025-11-05"
    assert apeseg["end_date"] == "2026-11-05"
    assert apeseg["certificates_count"] == 6


def test_merge_insurance_sbs_and_apeseg(sbs_sample, apeseg_sample):
    """Prueba consolidación de SBS y APESEG en InsuranceSchema (source='SBS + APESEG')."""
    sbs_res = SourceResult(source="SBS", status="ok", data=sbs_sample)
    apeseg_res = SourceResult(source="APESEG", status="ok", data=apeseg_sample)

    merged = merge_insurance_sources(sbs_res, apeseg_res)

    assert isinstance(merged, Insurance)
    assert merged.status == "ok"
    assert merged.source == "SBS + APESEG"
    assert merged.has_active_soat is True
    assert merged.company == "La Positiva"
    assert merged.policy_number == "000142242589000000000000"
    assert merged.start_date == "2025-11-05"
    assert merged.end_date == "2026-11-05"
    assert merged.accident_count == 0
    assert merged.policy_count == 6


def test_merge_graceful_degradation():
    """Prueba que si SBS da error pero APESEG responde, no falla el schema."""
    sbs_err = SourceResult(source="SBS", status="error", error="timeout")
    apeseg_ok = {
        "found": True,
        "has_active_soat": True,
        "active": {"company": "Pacifico", "status": "VIGENTE", "start_date": "2026-01-01"},
    }

    merged = merge_insurance_sources(sbs_err, apeseg_ok)
    assert merged.status == "ok"
    assert merged.has_active_soat is True
    assert merged.company == "Pacifico"
    assert merged.accident_count == 0
    assert merged.source == "SBS + APESEG"
