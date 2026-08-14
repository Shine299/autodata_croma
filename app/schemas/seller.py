from pydantic import Field

from app.schemas.common import CamelModel, Flag, SourceStatus, SourceSummary


class SellerScreeningRequest(CamelModel):
    document_type: str
    document_number: str
    claimed_role: str
    consent: bool


class Taxpayer(CamelModel):
    status: SourceStatus
    found: bool = False
    name: str | None = None
    ruc: str | None = None
    taxpayer_status: str | None = None
    condition: str | None = None
    main_activity: str | None = None
    is_vehicle_trader: bool = False
    registered_at: str | None = None
    source: str = "SUNAT"


class PersonalDebt(CamelModel):
    status: SourceStatus
    has_debt: bool = False
    currency: str = "PEN"
    total: float = 0
    item_count: int = 0
    related_plates: list[str] = Field(default_factory=list)
    source: str = "SAT_LIMA"


class SellerScreeningResponse(CamelModel):
    screening_id: str
    document_type: str
    document_masked: str
    created_at: str
    taxpayer: Taxpayer
    personal_debt: PersonalDebt
    flags: list[Flag] = Field(default_factory=list)
    sources_summary: list[SourceSummary] = Field(default_factory=list)
