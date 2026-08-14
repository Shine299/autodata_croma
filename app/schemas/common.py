from enum import Enum

from pydantic import BaseModel, ConfigDict


class CamelModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda s: "".join(
            w if i == 0 else w.capitalize() for i, w in enumerate(s.split("_"))
        ),
    )


class Verdict(str, Enum):
    GO = "GO"
    CAUTION = "CAUTION"
    STOP = "STOP"


class SourceStatus(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    ERROR = "error"
    SKIPPED = "skipped"


class DocumentType(str, Enum):
    DNI = "DNI"
    RUC = "RUC"
    CE = "CE"


class FlagCode(str, Enum):
    CAPTURE_ORDER = "CAPTURE_ORDER"
    SOAT_EXPIRED = "SOAT_EXPIRED"
    SOAT_MISSING = "SOAT_MISSING"
    HIGH_ACCIDENTS = "HIGH_ACCIDENTS"
    ACCIDENTS = "ACCIDENTS"
    HIGH_DEBT = "HIGH_DEBT"
    DEBT = "DEBT"
    SEVERE_INFRACTION = "SEVERE_INFRACTION"
    SELLER_IS_DEALER = "SELLER_IS_DEALER"
    SELLER_HAS_DEBT = "SELLER_HAS_DEBT"
    SELLER_NOT_FOUND = "SELLER_NOT_FOUND"
    SOURCES_UNAVAILABLE = "SOURCES_UNAVAILABLE"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SourceSummary(CamelModel):
    source: str
    status: SourceStatus
    latency_ms: int
    error: str | None = None


class Flag(CamelModel):
    code: FlagCode
    severity: Severity
    title: str
    detail: str
    source: str | None = None


class ErrorDetail(CamelModel):
    type: str
    code: str
    message: str
    request_id: str | None = None


class ErrorEnvelope(CamelModel):
    error: ErrorDetail
