"""E-01 — Tests de la página pública /r/{verificationId}."""

import json
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.repositories.verification_repo import VerificationRepository

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
async def client_with_seeded_verification():
    """Levanta una DB en memoria, siembra los 3 escenarios (GO/CAUTION/STOP) y
    devuelve un cliente HTTP contra la app real con `get_db` sobreescrito."""
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    seeded_ids = {}
    async with session_maker() as session:
        repo = VerificationRepository(session)
        for scenario in ("go", "caution", "stop"):
            payload = json.loads((FIXTURES_DIR / f"verification_{scenario}.json").read_text(encoding="utf-8"))
            vid = uuid.uuid4()
            await repo.save_verification(
                verification_id=vid,
                plate=payload["plate"],
                verdict=payload["verdict"],
                risk_score=payload["riskScore"],
                flags=payload["flags"],
                payload=payload,
            )
            seeded_ids[scenario] = str(vid)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, seeded_ids

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_report_page_go_shows_compra_and_no_flags(client_with_seeded_verification):
    client, ids = client_with_seeded_verification
    resp = await client.get(f"/r/{ids['go']}")
    assert resp.status_code == 200
    assert "COMPRA" in resp.text
    assert "ABC123" in resp.text
    assert "Hallazgos" not in resp.text  # sin flags, la sección no se renderiza


@pytest.mark.asyncio
async def test_report_page_caution_shows_ojo_and_flags(client_with_seeded_verification):
    client, ids = client_with_seeded_verification
    resp = await client.get(f"/r/{ids['caution']}")
    assert resp.status_code == 200
    assert "OJO" in resp.text
    assert "SOAT por vencer" in resp.text
    assert "algunas fuentes no respondieron" in resp.text  # confidence.capped=true


@pytest.mark.asyncio
async def test_report_page_stop_shows_no_compres_and_critical_flag(client_with_seeded_verification):
    client, ids = client_with_seeded_verification
    resp = await client.get(f"/r/{ids['stop']}")
    assert resp.status_code == 200
    assert "NO COMPRES" in resp.text
    assert "Orden de captura vigente" in resp.text


@pytest.mark.asyncio
async def test_report_page_unknown_id_returns_404_friendly_page(client_with_seeded_verification):
    client, _ids = client_with_seeded_verification
    resp = await client.get("/r/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "No encontramos esta verificación" in resp.text


@pytest.mark.asyncio
async def test_report_page_malformed_id_does_not_crash(client_with_seeded_verification):
    client, _ids = client_with_seeded_verification
    resp = await client.get("/r/not-a-uuid")
    assert resp.status_code == 404
