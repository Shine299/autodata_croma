from pydantic import BaseModel
from typing import List, Optional

from app.schemas.common import Verdict, Flag, FlagCode, Severity
from app.schemas.vehicle import VehicleInspectionResponse
from app.schemas.seller import SellerScreeningResponse

class ScoringResult(BaseModel):
    verdict: Verdict
    risk_score: int
    flags: List[Flag]
    headline: str
    summary: str


def calculate_score(
    vehicle: VehicleInspectionResponse,
    seller: Optional[SellerScreeningResponse] = None,
    claimed_role: Optional[str] = None
) -> ScoringResult:
    flags = []
    risk_score = 0
    verdict = Verdict.GO

    # Regla 1: Orden de captura (CRÍTICO -> STOP)
    if vehicle.capture_order.has_capture_order:
        verdict = Verdict.STOP
        risk_score += 100
        flags.append(Flag(
            code=FlagCode.CAPTURE_ORDER,
            severity=Severity.CRITICAL,
            title="Orden de captura",
            detail="Vehículo con orden de captura vigente",
            source="SAT_LIMA"
        ))

    # Regla 2: Siniestros (>= 2 -> mínimo CAUTION)
    if vehicle.insurance.accident_count >= 2:
        if verdict == Verdict.GO:
            verdict = Verdict.CAUTION
        risk_score += 30
        flags.append(Flag(
            code=FlagCode.HIGH_ACCIDENTS,
            severity=Severity.WARNING,
            title="Alta siniestralidad",
            detail=f"{vehicle.insurance.accident_count} siniestros reportados en los últimos 5 años",
            source="SBS + APESEG"
        ))

    # Regla 3: Deuda total > 1000 (mínimo CAUTION)
    total_debt = vehicle.tax_debt.total + vehicle.infractions.total
    if total_debt > 1000:
        if verdict == Verdict.GO:
            verdict = Verdict.CAUTION
        risk_score += 20
        flags.append(Flag(
            code=FlagCode.HIGH_DEBT,
            severity=Severity.WARNING,
            title="Alta deuda pendiente",
            detail=f"Deuda total de S/ {total_debt:.2f}",
            source="SUTRAN/CALLAO/SAT"
        ))

    # Regla 4: SOAT no vigente (mínimo CAUTION)
    if not vehicle.insurance.has_active_soat:
        if verdict == Verdict.GO:
            verdict = Verdict.CAUTION
        risk_score += 20
        flags.append(Flag(
            code=FlagCode.SOAT_EXPIRED,
            severity=Severity.WARNING,
            title="SOAT no vigente",
            detail="El vehículo no cuenta con SOAT activo",
            source="SBS + APESEG"
        ))

    # Regla 5: Vendedor revendedor haciéndose pasar por particular (mínimo CAUTION)
    if seller and claimed_role == "PARTICULAR" and seller.taxpayer.is_vehicle_trader:
        if verdict == Verdict.GO:
            verdict = Verdict.CAUTION
        risk_score += 30
        flags.append(Flag(
            code=FlagCode.SELLER_IS_DEALER,
            severity=Severity.WARNING,
            title="Posible revendedor",
            detail="El vendedor se declara particular pero tiene actividad comercial vehicular",
            source="SUNAT"
        ))

    # Regla 6: 2 o más fuentes fallaron (máximo CAUTION)
    error_count = sum(1 for s in vehicle.sources_summary if s.status == "error")
    if seller:
        error_count += sum(1 for s in seller.sources_summary if s.status == "error")
    
    if error_count >= 2:
        if verdict == Verdict.GO:
            verdict = Verdict.CAUTION
        flags.append(Flag(
            code=FlagCode.SOURCES_UNAVAILABLE,
            severity=Severity.WARNING,
            title="Fuentes caídas",
            detail="No se pudo consultar información en varias fuentes oficiales",
            source="Sistema"
        ))

    # Cap risk score at 100
    risk_score = min(100, risk_score)

    # Determinar titular y resumen
    if verdict == Verdict.GO:
        headline = "Todo en orden"
        summary = "No se encontraron problemas graves. Es una compra segura."
    elif verdict == Verdict.CAUTION:
        headline = "Revisar con cuidado"
        summary = "El vehículo tiene observaciones importantes que debes considerar antes de comprar."
    else:
        headline = "Evitar compra"
        summary = "Se encontraron problemas críticos que impiden la compra segura."

    return ScoringResult(
        verdict=verdict,
        risk_score=risk_score,
        flags=flags,
        headline=headline,
        summary=summary
    )
