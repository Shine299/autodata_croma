import json
from pathlib import Path
import pytest

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sunat import (
    is_vehicle_trader_activity,
    map_sunat_taxpayer,
)
from app.schemas.common import SourceStatus

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_map_sunat_sample_not_dealer():
    data = json.loads((FIXTURES_DIR / "sunat_sample.json").read_text())
    result = SourceResult(source="sunat", status="ok", data=data)
    taxpayer = map_sunat_taxpayer(result)

    assert taxpayer.status == SourceStatus.OK
    assert taxpayer.found is True
    assert taxpayer.ruc == "10456789012"
    assert taxpayer.name == "JUAN CARLOS PEREZ GOMEZ"
    assert taxpayer.taxpayer_status == "ACTIVO"
    assert taxpayer.condition == "HABIDO"
    assert taxpayer.is_vehicle_trader is False
    assert taxpayer.source == "SUNAT"


def test_map_sunat_dealer():
    data = json.loads((FIXTURES_DIR / "sunat_20100100101.json").read_text())
    result = SourceResult(source="sunat", status="ok", data=data)
    taxpayer = map_sunat_taxpayer(result)

    assert taxpayer.status == SourceStatus.OK
    assert taxpayer.found is True
    assert taxpayer.ruc == "20100100101"
    assert taxpayer.name == "AUTOMOTORES DEL SUR S.A.C."
    assert taxpayer.is_vehicle_trader is True


def test_is_vehicle_trader_keywords():
    assert is_vehicle_trader_activity("VENTA DE VEHICULOS AUTOMOTORES") is True
    assert is_vehicle_trader_activity("Comercio de vehiculos automotores") is True
    assert is_vehicle_trader_activity("CIIU 4510 - Venta de automoviles") is True
    assert is_vehicle_trader_activity("CONCESIONARIO Y TALLER") is True
    assert is_vehicle_trader_activity("ACTIVIDADES DE CONSULTORIA") is False
    assert is_vehicle_trader_activity(None) is False


def test_map_sunat_not_found():
    result = SourceResult(source="sunat", status="not_found", data={"found": False})
    taxpayer = map_sunat_taxpayer(result)

    assert taxpayer.status == SourceStatus.NOT_FOUND
    assert taxpayer.found is False
    assert taxpayer.ruc is None


def test_map_sunat_error_graceful():
    result = SourceResult(source="sunat", status="error", error="timeout")
    taxpayer = map_sunat_taxpayer(result)

    assert taxpayer.status == SourceStatus.ERROR
    assert taxpayer.found is False
