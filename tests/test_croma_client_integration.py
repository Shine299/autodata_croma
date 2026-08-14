import httpx
import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.integrations.croma.client import CromaClient
from app.repositories.models import CromaCacheModel, QuotaLogModel

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def integration_db():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def test_live_settings():
    with patch("app.integrations.croma.client.settings") as s:
        s.croma_mode = "live"
        s.croma_base_url = "https://api.croma.run"
        s.croma_api_key = "test-key"
        s.croma_timeout_seconds = 5
        yield s


def _make_mock_transport(responses: list[httpx.Response]):
    idx = {"i": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        resp = responses[idx["i"]]
        idx["i"] += 1
        return resp

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_croma_client_read_through_cache(test_live_settings, integration_db):
    payload = {"plate": "ABC123", "data": {"soat": True}}
    
    # 1. Primera llamada: Caché miss. Debe llamar a la API y guardar en base de datos.
    # Configuramos el transporte HTTP para retornar el payload.
    transport = _make_mock_transport([
        httpx.Response(200, json=payload, headers={"X-RateLimit-Remaining": "90", "X-Request-Id": "req-1"}),
    ])
    
    client = CromaClient(db=integration_db)
    client._client = httpx.AsyncClient(transport=transport, base_url="https://api.croma.run")

    result1 = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "ABC123"})
    
    assert result1.status == "ok"
    assert result1.data == payload
    assert result1.from_cache is False  # Fue llamado de red

    # 2. Segunda llamada: Caché hit. Debe recuperar de base de datos sin tocar la red.
    # Si intentara tocar la red, fallaría porque no configuramos más respuestas en el mock transport.
    result2 = await client.call("SBS", "/pe/sbs/soat/v1", {"plate": "ABC123"})
    
    assert result2.status == "ok"
    assert result2.data == payload
    assert result2.from_cache is True  # Fue recuperado de caché

    await client.close()
