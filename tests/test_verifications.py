import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.verifications import router

app.include_router(router, prefix="/api/v1")
client = TestClient(app)

def test_verification_go():
    resp = client.post("/api/v1/verifications", json={"plate": "ABC123_GO"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "GO"

def test_verification_stop():
    resp = client.post("/api/v1/verifications", json={"plate": "ABC123_STOP"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "STOP"

def test_verification_caution():
    resp = client.post("/api/v1/verifications", json={"plate": "ABC123_CAUTION"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "CAUTION"

def test_verification_seller_dealer():
    resp = client.post("/api/v1/verifications", json={
        "plate": "ABC123_GO",
        "seller": {
            "documentType": "DNI",
            "documentNumber": "12345678_DEALER",
            "claimedRole": "PARTICULAR",
            "consent": True
        }
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "CAUTION"
