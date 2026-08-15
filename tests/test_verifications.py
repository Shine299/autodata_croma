import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.verifications import router

app.include_router(router, prefix="/api/v1")
client = TestClient(app)

def test_verification_go():
    resp = client.post("/api/v1/verifications", json={"plate": "D0H741"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "GO"

def test_verification_stop():
    resp = client.post("/api/v1/verifications", json={"plate": "JKL012"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "STOP"

def test_verification_caution():
    resp = client.post("/api/v1/verifications", json={"plate": "DEF456"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "CAUTION"

def test_verification_seller_dealer():
    # Documento que resuelve la fixture de revendedor (sunat_20100100101.json →
    # is_vehicle_trader=True). El screening real vía perform_seller_screening detecta
    # SELLER_IS_DEALER y el veredicto baja a CAUTION.
    resp = client.post("/api/v1/verifications", json={
        "plate": "D0H741",
        "seller": {
            "documentType": "RUC",
            "documentNumber": "20100100101",
            "claimedRole": "PARTICULAR",
            "consent": True
        }
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["verdict"] == "CAUTION"


def test_verification_seller_requires_consent():
    resp = client.post("/api/v1/verifications", json={
        "plate": "D0H741",
        "seller": {
            "documentType": "DNI",
            "documentNumber": "10456789",
            "claimedRole": "PARTICULAR",
            "consent": False
        }
    })
    assert resp.status_code == 400


def test_appraisal_uses_provided_plate():
    # D-09: la tasación debe usar la placa enviada, no la placa demo por defecto.
    # JKL012 tiene orden de captura → fair_price 0 y NO_COMPRAR.
    resp = client.post(
        "/api/v1/verifications/00000000-0000-0000-0000-000000000000/appraisals",
        json={"askingPrice": 30000, "plate": "JKL012"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["fairPrice"] == 0.0
    assert data["recommendation"] == "NO_COMPRAR"
