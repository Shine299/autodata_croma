"""D-02 — Repositorio de estado de conversación del bot.

Persiste el estado de la máquina (`app/bot/states.py`) y el contexto acumulado
(placa, precio, etc.) en la tabla `conversations`, con `chat_id` como PK. Sigue el
patrón upsert-por-PK de `app/repositories/cache_repo.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import INITIAL, State
from app.repositories.models import ConversationModel


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._db = session

    async def get(self, chat_id: Union[str, int]) -> Tuple[State, Dict[str, Any]]:
        """Devuelve (estado, contexto) del chat. Si no existe, (IDLE, {})."""
        stmt = select(ConversationModel).where(ConversationModel.chat_id == str(chat_id))
        result = await self.session.execute(stmt)
        row = result.scalars().first()

        if row is None:
            return INITIAL, {}
        try:
            return State(row.state), dict(row.context or {})
        except ValueError:
            return INITIAL, dict(row.context or {})

    async def set(
        self,
        chat_id: Union[str, int],
        state: Union[State, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inserta o actualiza el estado y contexto del chat."""
        cid = str(chat_id)
        state_val = state.value if isinstance(state, State) else str(state)
        context_val = context if context is not None else {}
        now = datetime.now(timezone.utc)

        stmt = select(ConversationModel).where(ConversationModel.chat_id == cid)
        result = await self.session.execute(stmt)
        row = result.scalars().first()

        if row:
            row.state = state_val
            if context is not None:
                row.context = context_val
            row.updated_at = now
        else:
            self.session.add(
                ConversationModel(
                    chat_id=cid,
                    state=state_val,
                    context=context_val,
                    updated_at=now,
                )
            )

        await self.session.commit()

    async def reset(self, chat_id: Union[str, int]) -> None:
        """Vuelve el chat a IDLE con contexto vacío (botón 'Nueva consulta')."""
        await self.set(chat_id, INITIAL, {})

    # Aliases for compatibility
    async def get_state(self, chat_id: Union[str, int]) -> tuple[str, dict[str, Any]]:
        state, ctx = await self.get(chat_id)
        return state.value if isinstance(state, State) else str(state), ctx

    async def set_state(
        self,
        chat_id: Union[str, int],
        state: Union[State, str],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        await self.set(chat_id, state, context)

    async def clear_state(self, chat_id: Union[str, int]) -> None:
        await self.reset(chat_id)
