"""Verification repository for AutoData (Supabase / Postgres).

Handles persisting and retrieving full verification reports, enforcing privacy
rules (seller documents are strictly hashed via SHA-256 before storage — Art. VI).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import VerificationModel
from app.services.plate import normalize_plate, is_valid_plate


def hash_document(doc_number: str | None) -> str | None:
    """Generates a SHA-256 hash of a document number for ethical storage."""
    if not doc_number:
        return None
    cleaned = doc_number.strip().upper()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


class VerificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save_verification(
        self,
        verification_id: str | uuid.UUID,
        plate: str,
        verdict: str,
        risk_score: int,
        flags: list[dict[str, Any]],
        payload: dict[str, Any],
        seller_document: str | None = None,
        asking_price: float | None = None,
        channel: str | None = "api",
    ) -> VerificationModel:
        """Persists a full verification record."""
        v_uuid = uuid.UUID(str(verification_id)) if isinstance(verification_id, str) else verification_id
        seller_hash = hash_document(seller_document)
        clean_plate = normalize_plate(plate) if is_valid_plate(plate) else plate.strip().upper().replace("-", "")

        record = VerificationModel(
            id=v_uuid,
            plate=clean_plate,
            seller_hash=seller_hash,
            asking_price=asking_price,
            verdict=verdict,
            risk_score=risk_score,
            flags=flags,
            payload=payload,
            channel=channel,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)
        return record

    async def get_by_id(self, verification_id: str | uuid.UUID) -> dict[str, Any] | None:
        """Retrieves verification payload by its UUID."""
        try:
            v_uuid = uuid.UUID(str(verification_id)) if isinstance(verification_id, str) else verification_id
        except (ValueError, TypeError):
            return None

        query = select(VerificationModel).where(VerificationModel.id == v_uuid)
        result = await self._db.execute(query)
        record = result.scalars().first()
        if not record:
            return None
        return record.payload

    async def get_model_by_id(self, verification_id: str | uuid.UUID) -> VerificationModel | None:
        """Retrieves raw ORM VerificationModel by its UUID."""
        try:
            v_uuid = uuid.UUID(str(verification_id)) if isinstance(verification_id, str) else verification_id
        except (ValueError, TypeError):
            return None

        query = select(VerificationModel).where(VerificationModel.id == v_uuid)
        result = await self._db.execute(query)
        return result.scalars().first()

    async def get_by_plate(self, plate: str, limit: int = 5) -> list[dict[str, Any]]:
        """Retrieves recent verification payloads for a specific plate."""
        clean_plate = normalize_plate(plate) if is_valid_plate(plate) else plate.strip().upper().replace("-", "")
        query = (
            select(VerificationModel)
            .where(VerificationModel.plate == clean_plate)
            .order_by(VerificationModel.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(query)
        records = result.scalars().all()
        return [r.payload for r in records]
