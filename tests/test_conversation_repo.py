"""D-02 — Tests del repositorio de estado de conversación.

El test estrella (`test_state_survives_process_restart`) escribe el estado con un engine,
lo cierra y abre un engine NUEVO sobre el mismo archivo sqlite: eso reproduce un reinicio
del proceso y prueba el DoD ("el estado sobrevive a un reinicio").
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.bot.handlers import next_state
from app.bot.states import State
from app.core.database import Base
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.conversation import Extracted


def _make_maker(db_path: str):
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return engine, maker


@pytest.mark.asyncio
async def test_set_and_get_roundtrip(tmp_path):
    engine, maker = _make_maker(tmp_path / "conv.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with maker() as session:
        repo = ConversationRepository(session)
        # Default para un chat nuevo.
        state, ctx = await repo.get("chat-1")
        assert state is State.IDLE
        assert ctx == {}

        await repo.set("chat-1", State.AWAITING_PRICE, {"plate": "ABC123"})
        state, ctx = await repo.get("chat-1")
        assert state is State.AWAITING_PRICE
        assert ctx == {"plate": "ABC123"}

    await engine.dispose()


@pytest.mark.asyncio
async def test_state_survives_process_restart(tmp_path):
    db_path = tmp_path / "conv.db"

    # --- "Proceso 1": crea el esquema y guarda el estado, luego cierra el engine.
    engine1, maker1 = _make_maker(db_path)
    async with engine1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with maker1() as session:
        await ConversationRepository(session).set(
            "chat-42", State.AWAITING_PRICE, {"plate": "XYZ789"}
        )
    await engine1.dispose()

    # --- "Proceso 2": engine totalmente nuevo sobre el MISMO archivo.
    engine2, maker2 = _make_maker(db_path)
    async with maker2() as session:
        state, ctx = await ConversationRepository(session).get("chat-42")
    await engine2.dispose()

    assert state is State.AWAITING_PRICE
    assert ctx == {"plate": "XYZ789"}


@pytest.mark.asyncio
async def test_reset_returns_to_idle(tmp_path):
    engine, maker = _make_maker(tmp_path / "conv.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with maker() as session:
        repo = ConversationRepository(session)
        await repo.set("chat-1", State.DONE, {"plate": "ABC123", "asking_price": 32000})
        await repo.reset("chat-1")
        state, ctx = await repo.get("chat-1")
        assert state is State.IDLE
        assert ctx == {}

    await engine.dispose()


# --- Transiciones (función pura next_state) -------------------------------

def test_transition_plate_moves_to_awaiting_price():
    state, ctx, reply = next_state(State.IDLE, Extracted(plate="ABC123"), {})
    assert state is State.AWAITING_PRICE
    assert ctx["plate"] == "ABC123"
    assert "ABC123" in reply


def test_transition_price_after_plate_moves_to_done():
    state, ctx, reply = next_state(
        State.AWAITING_PRICE, Extracted(asking_price=32000), {"plate": "ABC123"}
    )
    assert state is State.DONE
    assert ctx["asking_price"] == 32000


def test_transition_plate_and_price_in_one_message():
    state, ctx, _ = next_state(
        State.IDLE, Extracted(plate="ABC123", asking_price=32000), {}
    )
    assert state is State.DONE
    assert ctx == {"plate": "ABC123", "asking_price": 32000}


def test_transition_garbage_stays_and_asks_for_plate():
    state, ctx, reply = next_state(State.IDLE, Extracted(), {})
    assert state is State.IDLE
    assert ctx == {}
    assert "placa" in reply.lower()
