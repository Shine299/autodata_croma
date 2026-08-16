import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jobs import job_store
from app.repositories.verification_repo import VerificationRepository
from app.schemas.verification import VerificationRequest
from app.schemas.appraisal import AppraisalRequest
from app.services.vehicles import get_vehicle_inspection
from app.services.appraisal import calculate_appraisal
from app.services.verification_runner import (
    SOURCE_DISPLAYS,
    build_verification,
    run_verification_job,
)

router = APIRouter(tags=["Verifications"])

@router.post("/verifications/{verification_id}/appraisals", response_model=dict)
async def create_appraisal(
    verification_id: str,
    req: AppraisalRequest,
    db: AsyncSession = Depends(get_db),
):
    # D-09: tasar la placa REAL. Prioridad: (1) la placa que manda el request; (2) la
    # placa de la verificación guardada (C-08); (3) fallback de demo como último recurso.
    plate = req.plate
    if not plate:
        try:
            payload = await VerificationRepository(db).get_by_id(verification_id)
            if payload:
                plate = payload.get("plate")
        except Exception:
            plate = None
    if not plate:
        plate = "D0H-741"

    vehicle = await get_vehicle_inspection(plate)

    appraisal = calculate_appraisal(
        verification_id=verification_id,
        vehicle=vehicle,
        asking_price=req.asking_price,
        tone=req.tone
    )
    return {"data": appraisal.model_dump(by_alias=True)}

@router.post("/verifications", response_model=dict)
async def create_verification(
    req: VerificationRequest,
    prefer: str | None = Header(default=None),
):
    """C-05 — Verificación completa (vehículo + vendedor + score).

    Gate ético (Art. VI): si viene un vendedor sin consentimiento explícito → 400.

    C-09 — Con `Prefer: respond-async` responde 202 y encola un job; el bot lo pollea
    y muestra el progreso fuente por fuente (D-05). Sin el header, corre síncrono.

    Toda la orquestación real vive en `build_verification` (compartida sync/async), que
    consulta Croma en vivo para las 6 fuentes del vehículo y, si aplica, al vendedor.
    """
    if req.seller and not req.seller.consent:
        raise HTTPException(status_code=400, detail="consent_required")

    # C-09: modo asíncrono (progreso incremental para D-05).
    if prefer and "respond-async" in prefer.lower():
        job = job_store.create(SOURCE_DISPLAYS)
        asyncio.create_task(run_verification_job(job.job_id, req))
        return JSONResponse(
            status_code=202,
            content={
                "data": {
                    "jobId": job.job_id,
                    "status": "pending",
                    "pollUrl": f"/api/v1/jobs/{job.job_id}",
                }
            },
        )

    # Modo síncrono.
    resp = await build_verification(req)
    return {"data": resp.model_dump(by_alias=True)}


@router.get("/verifications/{verification_id}", response_model=dict)
async def get_verification(
    verification_id: str,
    db: AsyncSession = Depends(get_db),
):
    """C-08 — Recupera una verificación guardada por su id.

    404 → el handler global lo convierte en el envelope `{"error": {...}}`.
    """
    payload = await VerificationRepository(db).get_by_id(verification_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="verification_not_found")
    return {"data": payload}
