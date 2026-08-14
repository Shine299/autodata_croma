from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel, Flag, Verdict


class SellerInput(CamelModel):
    document_type: str
    document_number: str
    claimed_role: str
    consent: bool


class VerificationRequest(CamelModel):
    plate: str
    asking_price: float | None = None
    currency: str = "PEN"
    seller: SellerInput | None = None
    channel: str = "api"


class Confidence(CamelModel):
    verified_sources: int
    total_sources: int
    capped: bool = False


class VerificationResponse(CamelModel):
    verification_id: str
    created_at: str
    plate: str
    verdict: Verdict
    risk_score: int
    headline: str
    summary: str
    flags: list[Flag] = Field(default_factory=list)
    vehicle: dict[str, Any] | None = None
    seller: dict[str, Any] | None = None
    appraisal: dict[str, Any] | None = None
    confidence: Confidence
    report_url: str
    disclaimer: str
