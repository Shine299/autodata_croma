"""C-09 (enqueue) — Ejecución asíncrona de una verificación como job.

Pieza que faltaba del modo async: el `job_store` (`app/core/jobs.py`) y `GET /jobs/{id}`
ya existían, pero nadie encolaba ni corría un job. Aquí vive:

- `build_verification`: el armado del `VerificationResponse` (extraído del endpoint
  síncrono para no duplicar la lógica entre el path sync y el async).
- `run_verification_job`: corre la verificación en background marcando cada fuente
  conforme se resuelve, para que el polling vea progreso incremental (DoD C-09).

Frontera de negocio de P1 (orquestación/resiliencia): el contrato y dónde se marca el
progreso se decidió a mano; solo el boilerplate es delegable (07-AGENTS).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.core.jobs import job_store
from app.integrations.croma.client import CromaClient
from app.schemas.seller import SellerScreeningRequest
from app.schemas.verification import Confidence, VerificationRequest, VerificationResponse
from app.services.appraisal import calculate_appraisal
from app.services.scoring import calculate_score
from app.services.seller import perform_seller_screening
from app.services.vehicles import get_vehicle_inspection

# Las 6 fuentes oficiales que se consultan (nombres visibles, alineados al orquestador).
SOURCE_DISPLAYS = ["SBS", "APESEG", "SUTRAN", "Callao", "SAT Lima", "SAT Capturas"]

# Latencia simulada por fuente en modo async, para que el polling observe el progreso
# fuente por fuente (en producción real la marca la latencia del orquestador). Los tests
# la ponen en 0 para correr rápido.
SOURCE_DELAY_SECONDS = 0.4


async def build_verification(req: VerificationRequest) -> VerificationResponse:
    """Arma el `VerificationResponse` a partir del request (lógica compartida sync/async)."""
    vehicle = await get_vehicle_inspection(req.plate)
    seller = None
    if req.seller:
        # D-08: screening REAL del vendedor vía Croma (SUNAT + SAT Lima).
        screening_req = SellerScreeningRequest(
            document_type=req.seller.document_type,
            document_number=req.seller.document_number,
            claimed_role=req.seller.claimed_role,
            consent=req.seller.consent,
        )
        # Sin sesión compartida: perform_seller_screening consulta 2 fuentes en paralelo
        # y un AsyncSession no es seguro concurrentemente. Consulta Croma directo.
        client = CromaClient()
        try:
            seller = await perform_seller_screening(screening_req, client)
        finally:
            await client.close()

    score = calculate_score(
        vehicle=vehicle,
        seller=seller,
        claimed_role=req.seller.claimed_role if req.seller else None,
    )

    verified_sources = sum(1 for s in vehicle.sources_summary if s.status != "error")
    total_sources = len(vehicle.sources_summary)
    if seller:
        verified_sources += sum(1 for s in seller.sources_summary if s.status != "error")
        total_sources += len(seller.sources_summary)

    verification_id = str(uuid.uuid4())

    # Si el cliente ya trajo el precio, calculamos aquí mismo la tasación (precio objetivo
    # = precio pedido − deducciones VERIFICADAS) para entregar el análisis en un solo paso.
    # No hay precio de mercado (Croma no lo da) → no se estima ningún valor de mercado.
    appraisal_dump = None
    if req.asking_price:
        appraisal_dump = calculate_appraisal(
            verification_id=verification_id,
            vehicle=vehicle,
            asking_price=req.asking_price,
        ).model_dump(by_alias=True)

    return VerificationResponse(
        verification_id=verification_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        plate=req.plate,
        verdict=score.verdict,
        risk_score=score.risk_score,
        headline=score.headline,
        summary=score.summary,
        flags=score.flags,
        vehicle=vehicle.model_dump(by_alias=True),
        seller=seller.model_dump(by_alias=True) if seller else None,
        appraisal=appraisal_dump,
        confidence=Confidence(
            verified_sources=verified_sources,
            total_sources=total_sources,
            capped=score.verdict == "CAUTION"
            and sum(1 for f in score.flags if f.code == "SOURCES_UNAVAILABLE") > 0,
        ),
        report_url=f"https://autodata.pe/r/{verification_id}",
        disclaimer="Reporte generado con fines referenciales.",
    )


async def run_verification_job(job_id: str, req: VerificationRequest) -> None:
    """Corre la verificación como job async, alimentando el `job_store` fuente por fuente.

    Marca cada una de las 6 fuentes como completada (con una pequeña latencia para que el
    polling vea el progreso subir 0→100), y al final guarda el veredicto o el error.
    """
    job_store.mark_running(job_id)
    try:
        resp = await build_verification(req)
        # Progreso incremental: una fuente a la vez (DoD C-09 / mensajes D-05).
        for source in SOURCE_DISPLAYS:
            if SOURCE_DELAY_SECONDS:
                await asyncio.sleep(SOURCE_DELAY_SECONDS)
            job_store.mark_source_done(job_id, source)
        job_store.complete(job_id, {"data": resp.model_dump(by_alias=True)})
    except Exception as exc:  # noqa: BLE001 — cualquier fallo se reporta como job fallido
        job_store.fail(
            job_id,
            {"type": "internal_error", "message": str(exc)},
        )
