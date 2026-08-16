"""E-08 — Tests del slide de límites conocidos y roadmap (/limites)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_limites_page_responds_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/limites")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_limites_page_declares_the_four_known_limits():
    """DoD E-08: honesto — los límites duros del producto deben estar declarados."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/limites")

    text = resp.text
    assert "SUNARP" in text
    assert "MTC" in text
    assert "mecánico" in text
    assert "asesoría legal" in text


@pytest.mark.asyncio
async def test_limites_page_has_roadmap_not_just_excuses():
    """DoD E-08: 'con plan, no una excusa' — debe haber roadmap, no solo límites."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/limites")

    text = resp.text
    assert "Roadmap" in text
    assert "QR" in text  # sello verificado
    assert "concesionarias" in text  # modelo de negocio
