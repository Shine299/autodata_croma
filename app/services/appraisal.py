import uuid
from typing import List
from app.schemas.appraisal import AppraisalResponse, Deduction
from app.schemas.vehicle import VehicleInspectionResponse

def calculate_appraisal(
    verification_id: str,
    vehicle: VehicleInspectionResponse,
    asking_price: float,
    tone: str = "cordial"
) -> AppraisalResponse:
    deductions: List[Deduction] = []
    
    # 1. Capture order
    if vehicle.capture_order.has_capture_order:
        return AppraisalResponse(
            appraisal_id=str(uuid.uuid4()),
            verification_id=verification_id,
            currency="PEN",
            asking_price=asking_price,
            fair_price=0.0,
            total_deduction=asking_price,
            deduction_pct=100.0,
            deductions=[],
            recommendation="NO_COMPRAR",
            negotiation_script="El vehículo tiene orden de captura. No recomiendo realizar la compra bajo ninguna circunstancia.",
            notes=["Vehículo con orden de captura. Precio justo es 0."]
        )
        
    # 2. Deuda transferible (100%)
    total_debt = vehicle.tax_debt.total + vehicle.infractions.total
    if total_debt > 0:
        deductions.append(Deduction(
            concept="Deuda transferible (papeletas + impuesto)",
            amount=total_debt,
            basis="100% del monto adeudado",
            source="SUTRAN/CALLAO/SAT"
        ))
        
    # 3. Siniestros (4% c/u, max 20%)
    accident_count = vehicle.insurance.accident_count
    if accident_count > 0:
        pct = min(20.0, accident_count * 4.0)
        amount = asking_price * (pct / 100.0)
        deductions.append(Deduction(
            concept="Depreciación por siniestros",
            amount=amount,
            basis=f"{pct}% del precio pedido ({accident_count} siniestros)",
            source="SBS"
        ))
        
    # 4. SOAT vencido (350 PEN)
    if not vehicle.insurance.has_active_soat:
        deductions.append(Deduction(
            concept="SOAT vencido",
            amount=350.0,
            basis="Costo estimado de renovación",
            source="SBS + APESEG"
        ))
        
    total_deduction = sum(d.amount for d in deductions)
    fair_price = max(0.0, asking_price - total_deduction)
    deduction_pct = (total_deduction / asking_price * 100) if asking_price > 0 else 0.0
    
    recommendation = "PRECIO_JUSTO" if total_deduction == 0 else "NEGOCIAR"
    
    # Negotiation script
    if recommendation == "PRECIO_JUSTO":
        script = "Hola. Revisé el reporte de AutoData y el auto está limpio. El precio me parece justo. Me gustaría coordinar para verlo."
    else:
        intro = "Hola. Estuve revisando el auto con AutoData." if tone == "cordial" else "Hola. El reporte oficial muestra problemas."
        script = f"{intro} Tiene algunas observaciones que suman S/ {total_deduction:.2f} en gastos extra. Mi oferta es de S/ {fair_price:.2f} para cerrar trato, asumiendo yo esos pendientes. ¿Qué te parece?"
        
    return AppraisalResponse(
        appraisal_id=str(uuid.uuid4()),
        verification_id=verification_id,
        currency="PEN",
        asking_price=asking_price,
        fair_price=fair_price,
        total_deduction=total_deduction,
        deduction_pct=deduction_pct,
        deductions=deductions,
        recommendation=recommendation,
        negotiation_script=script,
        notes=[]
    )
