from pydantic import Field

from app.schemas.common import CamelModel, SourceStatus, SourceSummary


class VehicleInspectionRequest(CamelModel):
    plate: str
    sources: list[str] | None = None
    force_refresh: bool = False


class Insurance(CamelModel):
    status: SourceStatus
    has_active_soat: bool = False
    company: str | None = None
    policy_number: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    accident_count: int = 0
    policy_count: int = 0
    data_through: str | None = None
    source: str = "SBS + APESEG"


class InfractionItem(CamelModel):
    document_number: str
    document_type: str
    document_date: str | None = None
    infraction_code: str
    classification: str
    source: str


class Infractions(CamelModel):
    status: SourceStatus
    has_infractions: bool = False
    count: int = 0
    currency: str = "PEN"
    total: float = 0
    severe_count: int = 0
    items: list[InfractionItem] = Field(default_factory=list)


class TaxDebtItem(CamelModel):
    concept: str
    period: str
    amount: float


class TaxDebt(CamelModel):
    status: SourceStatus
    has_debt: bool = False
    currency: str = "PEN"
    total: float = 0
    items: list[TaxDebtItem] = Field(default_factory=list)
    source: str = "SAT_LIMA"


class CaptureOrder(CamelModel):
    status: SourceStatus
    has_capture_order: bool = False
    issued_at: str | None = None
    reason: str | None = None
    source: str = "SAT_LIMA"


class VehicleInspectionResponse(CamelModel):
    inspection_id: str
    plate: str
    created_at: str
    from_cache: bool = False
    cached_at: str | None = None
    insurance: Insurance
    infractions: Infractions
    tax_debt: TaxDebt
    capture_order: CaptureOrder
    sources_summary: list[SourceSummary] = Field(default_factory=list)
    unverified_sources: list[str] = Field(default_factory=list)
