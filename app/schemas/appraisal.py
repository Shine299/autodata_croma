from pydantic import Field

from app.schemas.common import CamelModel


class AppraisalRequest(CamelModel):
    asking_price: float
    currency: str = "PEN"
    tone: str = "cordial"
    # D-09: placa real a tasar. Si no viene, el endpoint intenta recuperarla de la
    # verificación guardada (C-08) antes de caer a un valor por defecto de demo.
    plate: str | None = None


class Deduction(CamelModel):
    concept: str
    amount: float
    basis: str
    source: str


class AppraisalResponse(CamelModel):
    appraisal_id: str
    verification_id: str
    currency: str = "PEN"
    asking_price: float
    fair_price: float
    total_deduction: float
    deduction_pct: float
    deductions: list[Deduction] = Field(default_factory=list)
    recommendation: str
    negotiation_script: str
    notes: list[str] = Field(default_factory=list)
