import pytest
from unittest.mock import patch

from app.services.vehicles import get_vehicle_inspection


@pytest.fixture
def mock_settings():
    with patch("app.integrations.croma.client.settings") as s:
        s.croma_mode = "mock"
        s.croma_base_url = "https://api.croma.run"
        s.croma_api_key = ""
        s.croma_timeout_seconds = 5
        yield s


@pytest.mark.asyncio
async def test_clean_plate_returns_go_data(mock_settings):
    result = await get_vehicle_inspection("D0H741")
    assert result.plate == "D0H741"
    assert result.insurance.has_active_soat is True
    assert result.capture_order.has_capture_order is False
    assert result.infractions.total == 0
    assert result.tax_debt.total == 0.0
    assert len(result.sources_summary) == 6
    assert result.unverified_sources == []


@pytest.mark.asyncio
async def test_capture_plate_returns_stop_data(mock_settings):
    result = await get_vehicle_inspection("JKL012")
    assert result.capture_order.has_capture_order is True
    assert result.capture_order.reason is not None


@pytest.mark.asyncio
async def test_high_debt_plate(mock_settings):
    result = await get_vehicle_inspection("GHI789")
    assert result.infractions.total > 1000
    assert result.tax_debt.has_debt is True
    assert result.insurance.has_active_soat is False
