"""D-02 — Repositorio de estado de conversación del bot.

Persiste el estado de la máquina (`app/bot/states.py`) y el contexto acumulado
(placa, precio, etc.) en la tabla `conversations`, con `chat_id` como PK. Sigue el
patrón upsert-por-PK de `app/repositories/cache_repo.py`.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import INITIAL, State
from app.repositories.models import ConversationModel


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, chat_id: str) -> Tuple[State, Dict[str, Any]]:
        """Devuelve (estado, contexto) del chat. Si no existe, (IDLE, {})."""
        stmt = select(ConversationModel).where(ConversationModel.chat_id == str(chat_id))
        result = await self.session.execute(stmt)
        row = result.scalars().first()

        if row is None:
            return INITIAL, {}
        return State(row.state), dict(row.context or {})

    async def set(
        self,
        chat_id: str,
        state: State,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inserta o actualiza el estado y contexto del chat."""
        chat_id = str(chat_id)
        context = context or {}
        now = datetime.now(timezone.utc)

        stmt = select(ConversationModel).where(ConversationModel.chat_id == chat_id)
        result = await self.session.execute(stmt)
        row = result.scalars().first()

        if row:
            row.state = state.value
            row.context = context
            row.updated_at = now
        else:
            self.session.add(
                ConversationModel(
                    chat_id=chat_id,
                    state=state.value,
                    context=context,
                    updated_at=now,
                )
            )

        await self.session.commit()

    async def reset(self, chat_id: str) -> None:
        """Vuelve el chat a IDLE con contexto vacío (botón 'Nueva consulta')."""
        await self.set(chat_id, INITIAL, {})
