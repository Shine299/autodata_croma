import json
from pathlib import Path
import pytest

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sat_seller import map_sat_seller_debt
from app.schemas.common import SourceStatus

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_map_sat_seller_with_debt():
    data = json.loads((FIXTURES_DIR / "sat_seller_sample.json").read_text())
    result = SourceResult(source="sat_seller", status="ok", data=data)
    personal_debt = map_sat_seller_debt(result)

    assert personal_debt.status == SourceStatus.OK
    assert personal_debt.has_debt is True
    assert personal_debt.total == 1250.50
    assert personal_debt.item_count == 2
    assert "ABC123" in personal_debt.related_plates
    assert "XYZ789" in personal_debt.related_plates
    assert personal_debt.currency == "PEN"
    assert personal_debt.source == "SAT_LIMA"


def test_map_sat_seller_clean():
    data = json.loads((FIXTURES_DIR / "sat_seller_clean.json").read_text())
    result = SourceResult(source="sat_seller", status="ok", data=data)
    personal_debt = map_sat_seller_debt(result)

    assert personal_debt.status == SourceStatus.OK
    assert personal_debt.has_debt is False
    assert personal_debt.total == 0.0
    assert personal_debt.item_count == 0
    assert len(personal_debt.related_plates) == 0


def test_map_sat_seller_not_found():
    result = SourceResult(source="sat_seller", status="not_found", data={"found": False})
    personal_debt = map_sat_seller_debt(result)

    assert personal_debt.status == SourceStatus.NOT_FOUND
    assert personal_debt.has_debt is False
    assert personal_debt.total == 0.0


def test_map_sat_seller_error_graceful():
    result = SourceResult(source="sat_seller", status="error", error="http_500")
    personal_debt = map_sat_seller_debt(result)

    assert personal_debt.status == SourceStatus.ERROR
    assert personal_debt.has_debt is False
