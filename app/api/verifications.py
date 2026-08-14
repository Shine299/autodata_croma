"""C-08 — Verification Retrieval API Endpoint.

Provides GET /api/v1/verifications/{verification_id} to retrieve previously
generated verification reports from persistent storage.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.verification_repo import VerificationRepository

router = APIRouter(prefix="/verifications", tags=["verifications"])


@router.get("/{verification_id}", status_code=status.HTTP_200_OK)
async def get_verification_by_id(
    verification_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves an existing verification report by verification ID."""
    repo = VerificationRepository(db)
    payload = await repo.get_by_id(verification_id)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "type": "not_found",
                    "code": "verification_not_found",
                    "message": f"Verification report '{verification_id}' not found.",
                }
            },
        )

    # If payload already contains "data" envelope or is the data dict itself
    if isinstance(payload, dict) and "data" in payload:
        return payload

    return {"data": payload}
