"""Conversation repository for Telegram bot state persistence."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import ConversationModel


class ConversationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_state(self, chat_id: str | int) -> tuple[str, dict[str, Any]]:
        """Returns (state, context) for a chat_id."""
        cid = str(chat_id)
        query = select(ConversationModel).where(ConversationModel.chat_id == cid)
        result = await self._db.execute(query)
        record = result.scalars().first()
        if not record:
            return "IDLE", {}
        return record.state, record.context or {}

    async def set_state(
        self,
        chat_id: str | int,
        state: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Sets or updates the conversation state and context for a chat_id."""
        cid = str(chat_id)
        query = select(ConversationModel).where(ConversationModel.chat_id == cid)
        result = await self._db.execute(query)
        record = result.scalars().first()

        if record:
            record.state = state
            if context is not None:
                record.context = context
        else:
            record = ConversationModel(
                chat_id=cid,
                state=state,
                context=context or {},
            )
            self._db.add(record)

        await self._db.commit()

    async def clear_state(self, chat_id: str | int) -> None:
        """Resets the state to IDLE and clears context."""
        await self.set_state(chat_id, "IDLE", {})
