import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.schemas.verification import VerificationRequest, VerificationResponse, Confidence
from app.schemas.appraisal import AppraisalRequest, AppraisalResponse
from app.services.vehicles import get_vehicle_inspection
from app.services.sellers import get_seller_screening
from app.services.scoring import calculate_score
from app.services.appraisal import calculate_appraisal
from app.services.plate import normalize_plate

router = APIRouter(tags=["Verifications"])

@router.post("/verifications/{verification_id}/appraisals", response_model=dict)
async def create_appraisal(verification_id: str, req: AppraisalRequest):
    # ponytail: fetch from DB when C-08 is done, for now re-query the plate
    plate = getattr(req, "plate", None) or "D0H-741"
    vehicle = await get_vehicle_inspection(plate)

    appraisal = calculate_appraisal(
        verification_id=verification_id,
        vehicle=vehicle,
        asking_price=req.asking_price,
        tone=req.tone
    )
    return {"data": appraisal.model_dump(by_alias=True)}

@router.post("/verifications", response_model=dict)
async def create_verification(req: VerificationRequest):
    try:
        plate = normalize_plate(req.plate)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_plate")

    vehicle = await get_vehicle_inspection(plate)

    # D-10 caso 1: todas las fuentes devuelven not_found
    all_not_found = all(s.status == "not_found" for s in vehicle.sources_summary)
    if all_not_found:
        raise HTTPException(
            status_code=404,
            detail="No encontramos registros para esa placa. Verifica que este bien escrita."
        )

    seller = None
    if req.seller:
        if not req.seller.consent:
            raise HTTPException(status_code=400, detail="consent_required")
        seller = await get_seller_screening(req.seller.document_number)
    
    score = calculate_score(
        vehicle=vehicle,
        seller=seller,
        claimed_role=req.seller.claimed_role if req.seller else None
    )
    
    verified_sources = sum(1 for s in vehicle.sources_summary if s.status != "error")
    total_sources = len(vehicle.sources_summary)
    
    if seller:
        verified_sources += sum(1 for s in seller.sources_summary if s.status != "error")
        total_sources += len(seller.sources_summary)
        
    verification_id = str(uuid.uuid4())
    
    resp = VerificationResponse(
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
        appraisal=None,
        confidence=Confidence(
            verified_sources=verified_sources,
            total_sources=total_sources,
            capped=score.verdict == "CAUTION" and sum(1 for f in score.flags if f.code == "SOURCES_UNAVAILABLE") > 0
        ),
        report_url=f"https://autodata.pe/r/{verification_id}",
        disclaimer="Reporte generado con fines referenciales."
    )
    
    return {"data": resp.model_dump(by_alias=True)}
