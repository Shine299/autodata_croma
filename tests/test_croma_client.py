import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from app.integrations.croma.client import CromaClient
from app.integrations.croma.models import SourceResult

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def _make_transport(responses: list[httpx.Response]):
    idx = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        resp = responses[idx["i"]]
        idx["i"] += 1
        return resp

    return httpx.MockTransport(handler)


@pytest.fixture
def live_settings():
    with patch("app.integrations.croma.client.settings") as s:
        s.croma_mode = "live"
        s.croma_base_url = "https://api.croma.run"
        s.croma_api_key = "test-key"
        s.croma_timeout_seconds = 5
        yield s


@pytest.fixture
def mock_settings():
    with patch("app.integrations.croma.client.settings") as s:
        s.croma_mode = "mock"
        s.croma_base_url = "https://api.croma.run"
        s.croma_api_key = ""
        s.croma_timeout_seconds = 5
        yield s


@pytest.mark.asyncio
async def test_successful_call(live_settings):
    payload = {"plate": "ABC123", "data": {"soat": True}}
    transport = _make_transport([
        httpx.Response(200, json=payload, headers={"X-RateLimit-Remaining": "99"}),
    ])
    client = CromaClient()
    client._client = httpx.AsyncClient(transport=transport, base_url="https://api.croma.run")

    result = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "ABC123"})

    assert result.status == "ok"
    assert result.data == payload
    assert result.from_cache is False
    assert result.latency_ms >= 0
    await client.close()


@pytest.mark.asyncio
async def test_429_retry_then_success(live_settings):
    payload = {"plate": "ABC123"}
    transport = _make_transport([
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(200, json=payload),
    ])
    client = CromaClient()
    client._client = httpx.AsyncClient(transport=transport, base_url="https://api.croma.run")

    result = await client.call("SUTRAN", "/pe/sutran/infracciones/v1", {"plate": "ABC123"})

    assert result.status == "ok"
    assert result.data == payload
    await client.close()


@pytest.mark.asyncio
async def test_429_exhausts_retries(live_settings):
    transport = _make_transport([
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(429, headers={"Retry-After": "0"}),
    ])
    client = CromaClient()
    client._client = httpx.AsyncClient(transport=transport, base_url="https://api.croma.run")

    result = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "ABC123"})

    assert result.status == "error"
    assert result.error == "rate_limited"
    await client.close()


@pytest.mark.asyncio
async def test_mock_mode_reads_fixture(mock_settings, tmp_path):
    fixture = {"plate": "ABC123", "soat": True}
    fixture_file = tmp_path / "sbs_sample.json"
    fixture_file.write_text(json.dumps(fixture))

    with patch("app.integrations.croma.client.FIXTURES_DIR", tmp_path):
        client = CromaClient()
        result = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "XYZ789"})

    assert result.status == "ok"
    assert result.data == fixture
    assert result.from_cache is True
    await client.close()


@pytest.mark.asyncio
async def test_mock_mode_missing_fixture(mock_settings, tmp_path):
    with patch("app.integrations.croma.client.FIXTURES_DIR", tmp_path):
        client = CromaClient()
        result = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "NOPE"})

    assert result.status == "not_found"
    assert result.from_cache is True
    await client.close()


@pytest.mark.asyncio
async def test_http_error_returns_error_result(live_settings):
    transport = _make_transport([
        httpx.Response(500, text="Internal Server Error"),
    ])
    client = CromaClient()
    client._client = httpx.AsyncClient(transport=transport, base_url="https://api.croma.run")

    result = await client.call("SAT", "/pe/sat-lima/v1", {"plate": "ABC123"})

    assert result.status == "error"
    assert result.error == "http_500"
    await client.close()
