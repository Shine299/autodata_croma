import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db
from app.repositories.quota_repo import QuotaRepository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def api_db():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Dependency override
    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with session_maker() as session:
        yield session

    # Limpiar override
    app.dependency_overrides.clear()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_endpoint(api_db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    assert res_data["data"]["status"] == "ok"
    assert res_data["data"]["database"] == "connected"


@pytest.mark.asyncio
async def test_quota_endpoint(api_db):
    # Insertar algunos logs simulados usando QuotaRepository
    quota_repo = QuotaRepository(api_db)
    await quota_repo.log_quota(
        source="APESEG",
        endpoint="/pe/apeseg/soat/v1",
        remaining=95,
        request_id="req-quota-1",
        cache_hit=False,
        latency_ms=180
    )
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/quota")
        
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    quota_info = res_data["data"]
    assert quota_info["limit"] == 100
    assert quota_info["remaining"] == 95
    assert quota_info["consumedToday"] == 1
    assert quota_info["cacheHitRate"] == 0.0
