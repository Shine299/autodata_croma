import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.verification_repo import VerificationRepository, hash_document

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def memory_db_session():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_verification_repo_save_and_get(memory_db_session):
    repo = VerificationRepository(memory_db_session)
    vid = uuid.uuid4()
    sample_payload = {
        "verificationId": str(vid),
        "plate": "ABC123",
        "verdict": "GO",
        "riskScore": 10,
        "headline": "Vehículo en buen estado",
    }

    record = await repo.save_verification(
        verification_id=vid,
        plate="ABC123",
        verdict="GO",
        risk_score=10,
        flags=[],
        payload=sample_payload,
        seller_document="12345678",
        asking_price=25000.0,
    )

    assert record.seller_hash == hash_document("12345678")
    assert record.seller_hash != "12345678"  # Art. VI: Never plain text

    retrieved_payload = await repo.get_by_id(vid)
    assert retrieved_payload is not None
    assert retrieved_payload["plate"] == "ABC123"
    assert retrieved_payload["verdict"] == "GO"


@pytest.mark.asyncio
async def test_verification_repo_get_by_plate(memory_db_session):
    repo = VerificationRepository(memory_db_session)
    vid = uuid.uuid4()
    await repo.save_verification(
        verification_id=vid,
        plate="D0H741",
        verdict="CAUTION",
        risk_score=45,
        flags=[],
        payload={"verificationId": str(vid), "plate": "D0H741"},
    )

    results = await repo.get_by_plate("d0h-741")
    assert len(results) == 1
    assert results[0]["plate"] == "D0H741"


@pytest.mark.asyncio
async def test_conversation_repo_state(memory_db_session):
    repo = ConversationRepository(memory_db_session)
    chat_id = "987654321"

    # Default state is IDLE
    state, ctx = await repo.get_state(chat_id)
    assert state == "IDLE"
    assert ctx == {}

    # Transition to AWAITING_PRICE
    await repo.set_state(chat_id, "AWAITING_PRICE", {"plate": "ABC123"})
    state, ctx = await repo.get_state(chat_id)
    assert state == "AWAITING_PRICE"
    assert ctx.get("plate") == "ABC123"

    # Clear state
    await repo.clear_state(chat_id)
    state, ctx = await repo.get_state(chat_id)
    assert state == "IDLE"
    assert ctx == {}


@pytest.mark.asyncio
async def test_verifications_api_endpoints(memory_db_session):
    async def override_get_db():
        yield memory_db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Non-existent ID -> 404
            fake_id = str(uuid.uuid4())
            resp = await ac.get(f"/api/v1/verifications/{fake_id}")
            assert resp.status_code == 404
            assert resp.json()["detail"]["error"]["code"] == "verification_not_found"

            # 2. Existing ID -> 200
            repo = VerificationRepository(memory_db_session)
            vid = uuid.uuid4()
            await repo.save_verification(
                verification_id=vid,
                plate="ABC123",
                verdict="GO",
                risk_score=5,
                flags=[],
                payload={"verificationId": str(vid), "plate": "ABC123", "verdict": "GO"},
            )

            resp_ok = await ac.get(f"/api/v1/verifications/{vid}")
            assert resp_ok.status_code == 200
            assert resp_ok.json()["data"]["plate"] == "ABC123"
    finally:
        app.dependency_overrides.pop(get_db, None)
