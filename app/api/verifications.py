import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.jobs import job_store
from app.repositories.verification_repo import VerificationRepository
from app.schemas.verification import VerificationRequest
from app.schemas.appraisal import AppraisalRequest, AppraisalResponse
from app.services.vehicles import get_vehicle_inspection
from app.services.appraisal import calculate_appraisal
from app.services.verification_runner import (
    SOURCE_DISPLAYS,
    build_verification,
    run_verification_job,
)

router = APIRouter(tags=["Verifications"])

@router.post("/verifications/{verification_id}/appraisals", response_model=dict)
async def create_appraisal(verification_id: str, req: AppraisalRequest):
    # TODO: Fetch verification from DB using verification_id.
    # For now, we mock the vehicle fetching to allow testing the endpoint directly.
    vehicle = await get_vehicle_inspection("ABC123_CAUTION") # Mocked state
    
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
    """Crea una verificación.

    Modo síncrono (por defecto): devuelve el veredicto completo (200).
    Modo asíncrono (`Prefer: respond-async`, C-09): encola un job, devuelve 202 con
    `jobId` + `pollUrl` y corre la verificación en background alimentando el `job_store`.
    """
    if prefer and "respond-async" in prefer.lower():
        job = job_store.create(SOURCE_DISPLAYS)
        # Fire-and-forget: la verificación sigue en background; el cliente pollea el job.
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
