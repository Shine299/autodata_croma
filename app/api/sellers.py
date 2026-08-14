"""C-03 — Seller Screening API Endpoint.

Provides POST /api/v1/sellers/screenings adhering strictly to 03-API-DESIGN.md
and ethical consent validation (Art. VI).
"""

from __future__ import annotations

import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.integrations.croma.client import CromaClient, get_croma_client
from app.schemas.common import ErrorDetail, ErrorEnvelope
from app.schemas.seller import SellerScreeningRequest, SellerScreeningResponse
from app.services.seller import perform_seller_screening

router = APIRouter(prefix="/sellers", tags=["sellers"])


def validate_seller_request(request: SellerScreeningRequest) -> None:
    """Validates document numbers and consent compliance."""
    if not request.consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "validation_error",
                    "code": "consent_required",
                    "message": "User consent is required to perform seller screening under Peruvian personal data protection law (Art. VI).",
                }
            },
        )

    doc_type = request.document_type.strip().upper()
    doc_number = request.document_number.strip()

    if doc_type == "DNI" and not re.fullmatch(r"\d{8}", doc_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "validation_error",
                    "code": "invalid_document",
                    "message": "DNI must be exactly 8 digits.",
                }
            },
        )

    if doc_type == "RUC" and not re.fullmatch(r"\d{11}", doc_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "validation_error",
                    "code": "invalid_document",
                    "message": "RUC must be exactly 11 digits.",
                }
            },
        )


@router.post("/screenings", status_code=status.HTTP_200_OK)
async def create_seller_screening(
    request: SellerScreeningRequest,
    client: CromaClient = Depends(get_croma_client),
):
    """Executes a seller screening and returns risk profile + flags."""
    validate_seller_request(request)

    response: SellerScreeningResponse = await perform_seller_screening(request, client)
    return {"data": response.model_dump(by_alias=True)}
