"""C-03 — Seller Screening Service.

Executes seller verification across SUNAT (taxpayer status & dealer detection) and
SAT Lima (personal debt & related plates by document). Evaluates flags such as
SELLER_IS_DEALER, SELLER_HAS_DEBT and SELLER_NOT_FOUND. Enforces data protection masking.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import uuid

from app.integrations.croma.client import CromaClient
from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sunat import map_sunat_taxpayer
from app.integrations.croma.sources.sat_seller import map_sat_seller_debt
from app.schemas.common import Flag, FlagCode, Severity, SourceStatus, SourceSummary
from app.schemas.seller import (
    PersonalDebt,
    SellerScreeningRequest,
    SellerScreeningResponse,
    Taxpayer,
)


def mask_document(doc: str) -> str:
    """Masks all but the last 3 digits of a document number."""
    cleaned = doc.strip()
    if len(cleaned) <= 3:
        return "***"
    return ("*" * (len(cleaned) - 3)) + cleaned[-3:]


def evaluate_seller_flags(
    claimed_role: str,
    taxpayer: Taxpayer,
    personal_debt: PersonalDebt,
) -> list[Flag]:
    """Evaluates seller risk flags."""
    flags: list[Flag] = []
    role = claimed_role.strip().upper()

    # Flag estrella: SELLER_IS_DEALER
    if role in ("PARTICULAR", "INDIVIDUAL", "UNKNOWN") and taxpayer.is_vehicle_trader:
        flags.append(
            Flag(
                code=FlagCode.SELLER_IS_DEALER,
                severity=Severity.CRITICAL if role == "PARTICULAR" else Severity.WARNING,
                title="Vendedor identificado como revendedor comercial",
                detail="El vendedor declaró ser particular pero figura en SUNAT con actividad comercial de venta de vehículos.",
                source="SUNAT",
            )
        )

    # Flag: SELLER_HAS_DEBT
    if personal_debt.has_debt or personal_debt.total > 0:
        flags.append(
            Flag(
                code=FlagCode.SELLER_HAS_DEBT,
                severity=Severity.WARNING,
                title="Vendedor registra deuda tributaria personal en SAT",
                detail=(
                    f"Registra deuda personal de S/ {personal_debt.total:,.2f} en SAT Lima "
                    f"asociada a {personal_debt.item_count} concepto(s) y {len(personal_debt.related_plates)} placa(s)."
                ),
                source="SAT_LIMA",
            )
        )

    # Flag: SELLER_NOT_FOUND
    if (
        taxpayer.status == SourceStatus.NOT_FOUND
        and personal_debt.status == SourceStatus.NOT_FOUND
        and not taxpayer.found
        and not personal_debt.has_debt
    ):
        flags.append(
            Flag(
                code=FlagCode.SELLER_NOT_FOUND,
                severity=Severity.INFO,
                title="Documento no hallado en bases públicas consultadas",
                detail="No se encontraron registros activos de actividad comercial ni deudas para el documento proporcionado.",
                source="SUNAT + SAT_LIMA",
            )
        )

    return flags


async def perform_seller_screening(
    request: SellerScreeningRequest,
    client: CromaClient,
) -> SellerScreeningResponse:
    """Orchestrates seller screening across SUNAT and SAT Lima."""
    doc_number = request.document_number.strip()
    doc_type = request.document_type.strip().upper()
    body = {
        "document_type": doc_type,
        "document_number": doc_number,
    }

    # Concurrent fetch from SUNAT and SAT Seller
    sunat_task = client.call("sunat", "/api/v1/croma/sunat", body, cache_key=doc_number)
    sat_task = client.call("sat_seller", "/api/v1/croma/sat-seller", body, cache_key=doc_number)

    sunat_res, sat_res = await asyncio.gather(sunat_task, sat_task, return_exceptions=False)

    taxpayer = map_sunat_taxpayer(sunat_res)
    personal_debt = map_sat_seller_debt(sat_res)

    flags = evaluate_seller_flags(request.claimed_role, taxpayer, personal_debt)

    sources_summary: list[SourceSummary] = [
        SourceSummary(
            source="SUNAT",
            status=SourceStatus(sunat_res.status),
            latency_ms=sunat_res.latency_ms,
            error=sunat_res.error,
        ),
        SourceSummary(
            source="SAT_LIMA",
            status=SourceStatus(sat_res.status),
            latency_ms=sat_res.latency_ms,
            error=sat_res.error,
        ),
    ]

    return SellerScreeningResponse(
        screening_id=str(uuid.uuid4()),
        document_type=doc_type,
        document_masked=mask_document(doc_number),
        created_at=datetime.now(timezone.utc).isoformat(),
        taxpayer=taxpayer,
        personal_debt=personal_debt,
        flags=flags,
        sources_summary=sources_summary,
    )
