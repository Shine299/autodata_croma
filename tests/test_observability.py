import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_details():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json().get("data", {})
    assert data.get("status") == "ok"
    assert data.get("version") == "0.1.0"
    assert "environment" in data
    assert "uptimeSeconds" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_request_id_generated_and_returned_in_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-response-time" in response.headers
    assert len(response.headers["x-request-id"]) > 0


@pytest.mark.asyncio
async def test_custom_request_id_preserved():
    custom_id = "test-req-id-12345"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health", headers={"X-Request-Id": custom_id})

    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id
