import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_seller_screening_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/sellers/screenings",
            json={
                "documentType": "DNI",
                "documentNumber": "10456789",
                "claimedRole": "PARTICULAR",
                "consent": True,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    data = body["data"]

    assert data["documentType"] == "DNI"
    assert data["documentMasked"] == "*****789"
    assert "screeningId" in data
    assert "taxpayer" in data
    assert "personalDebt" in data
    assert "sourcesSummary" in data


@pytest.mark.asyncio
async def test_seller_screening_consent_required():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/sellers/screenings",
            json={
                "documentType": "DNI",
                "documentNumber": "10456789",
                "claimedRole": "PARTICULAR",
                "consent": False,
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["code"] == "consent_required"


@pytest.mark.asyncio
async def test_seller_screening_invalid_dni_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/sellers/screenings",
            json={
                "documentType": "DNI",
                "documentNumber": "123",  # Not 8 digits
                "claimedRole": "PARTICULAR",
                "consent": True,
            },
        )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "invalid_document"


@pytest.mark.asyncio
async def test_seller_screening_dealer_flag():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/sellers/screenings",
            json={
                "documentType": "RUC",
                "documentNumber": "20100100101",
                "claimedRole": "PARTICULAR",
                "consent": True,
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["taxpayer"]["isVehicleTrader"] is True
    codes = [f["code"] for f in data["flags"]]
    assert "SELLER_IS_DEALER" in codes
