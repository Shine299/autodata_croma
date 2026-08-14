import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.repositories.cache_repo import CacheRepository
from app.repositories.quota_repo import QuotaRepository
from app.repositories.models import CromaCacheModel, QuotaLogModel

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
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


@pytest.mark.asyncio
async def test_cache_repo_save_and_retrieve(test_db):
    cache_repo = CacheRepository(test_db)
    source = "SBS"
    key = "ABC123"
    payload = {"plate": "ABC123", "hasActiveSoat": True}

    # Guardar en caché con TTL de 1 hora
    await cache_repo.set_cached(source, key, payload, "ok", 3600)

    # Recuperar
    cached = await cache_repo.get_cached(source, key)
    assert cached == payload


@pytest.mark.asyncio
async def test_cache_repo_expiration(test_db):
    cache_repo = CacheRepository(test_db)
    source = "SUTRAN"
    key = "XYZ789"
    payload = {"infractions": []}

    # Guardar en caché con TTL de -10 segundos (ya expirado)
    await cache_repo.set_cached(source, key, payload, "ok", -10)

    # Recuperar (debe retornar None)
    cached = await cache_repo.get_cached(source, key)
    assert cached is None


@pytest.mark.asyncio
async def test_quota_repo_logging_and_summary(test_db):
    quota_repo = QuotaRepository(test_db)

    # 1. Loguear un hit de caché (no consume cuota de red)
    await quota_repo.log_quota(
        source="SBS",
        endpoint="/pe/sbs/soat/v1",
        remaining=None,
        request_id=None,
        cache_hit=True,
        latency_ms=0
    )

    # 2. Loguear un miss de caché (llamada real de red, consume cuota)
    await quota_repo.log_quota(
        source="SUTRAN",
        endpoint="/pe/sutran/infracciones/v1",
        remaining=98,
        request_id="req_123",
        cache_hit=False,
        latency_ms=250
    )

    # Obtener el resumen
    summary = await quota_repo.get_daily_summary(mode="live", limit=100)

    assert summary["limit"] == 100
    assert summary["consumedToday"] == 1  # Solo la llamada real
    assert summary["remaining"] == 98      # El reportado por el último log no nulo
    assert summary["cacheHitRate"] == 0.5  # 1 hit de 2 llamadas totales
    assert summary["mode"] == "live"
