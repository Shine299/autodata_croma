import pytest
import pytest_asyncio
from unittest.mock import patch

from app.integrations.croma.client import CromaClient
from app.integrations.croma.models import SourceResult
from app.integrations.croma.orchestrator import fetch_all_sources


@pytest.fixture
def mock_client():
    return CromaClient()


@pytest.mark.asyncio
async def test_happy_path_all_sources(mock_client):
    result = await fetch_all_sources(mock_client, "D0H-741")
    assert result.insurance.status in ("ok", "not_found")
    assert result.infractions is not None
    assert result.tax_debt is not None
    assert result.capture_order is not None
    assert len(result.sources_summary) == 6
    for s in result.sources_summary:
        assert s.status in ("ok", "not_found")
    assert result.total_latency_ms >= 0


@pytest.mark.asyncio
async def test_partial_failure_still_returns_other_sources(mock_client):
    original_mock = mock_client._mock_call

    def patched_mock(source, body):
        if source in ("sbs_soat", "callao"):
            return SourceResult(source=source, status="error", error="simulated")
        return original_mock(source, body)

    mock_client._mock_call = patched_mock
    result = await fetch_all_sources(mock_client, "D0H-741")
    assert result.infractions is not None
    assert result.tax_debt is not None
    assert result.capture_order is not None
    errors = [s.source for s in result.sources_summary if s.status == "error"]
    assert "SBS" in errors
    assert "Callao" in errors
    assert len(result.unverified_sources) >= 2


@pytest.mark.asyncio
async def test_invalid_plate_raises():
    client = CromaClient()
    with pytest.raises(ValueError, match="invalid_plate"):
        await fetch_all_sources(client, "INVALID")


@pytest.mark.asyncio
async def test_source_filtering(mock_client):
    result = await fetch_all_sources(mock_client, "D0H-741", sources=["sbs_soat", "sutran"])
    active = [s for s in result.sources_summary if s.status != "skipped"]
    skipped = [s for s in result.sources_summary if s.status == "skipped"]
    assert len(active) == 2
    assert len(skipped) == 4
