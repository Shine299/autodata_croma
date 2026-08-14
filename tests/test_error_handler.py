import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient

from app.main import app

_test_router = APIRouter(prefix="/test-errors")


@_test_router.get("/http404")
async def _raise_404():
    raise HTTPException(status_code=404, detail="not_found")


@_test_router.get("/http502")
async def _raise_502():
    raise HTTPException(status_code=502, detail="source_down")


@_test_router.get("/value-error")
async def _raise_value():
    raise ValueError("invalid_plate")


@_test_router.get("/unhandled")
async def _raise_generic():
    raise RuntimeError("boom")


app.include_router(_test_router)
client = TestClient(app, raise_server_exceptions=False)


def _assert_envelope(resp, expected_status, expected_type, expected_code):
    assert resp.status_code == expected_status
    body = resp.json()
    assert "error" in body
    err = body["error"]
    assert err["type"] == expected_type
    assert err["code"] == expected_code
    assert "message" in err
    assert "traceback" not in resp.text.lower()


def test_404_envelope():
    _assert_envelope(client.get("/test-errors/http404"), 404, "not_found", "not_found")


def test_502_envelope():
    _assert_envelope(client.get("/test-errors/http502"), 502, "upstream_error", "source_down")


def test_value_error_envelope():
    _assert_envelope(client.get("/test-errors/value-error"), 400, "validation_error", "invalid_plate")


def test_unhandled_returns_500_no_stacktrace():
    _assert_envelope(client.get("/test-errors/unhandled"), 500, "internal_error", "internal_error")


def test_real_404_uses_envelope():
    resp = client.get("/ruta-que-no-existe")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["type"] == "not_found"
