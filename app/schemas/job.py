from typing import Any

from pydantic import Field

from app.schemas.common import CamelModel


class JobResponse(CamelModel):
    job_id: str
    status: str
    progress: int = 0
    completed_sources: list[str] = Field(default_factory=list)
    pending_sources: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    created_at: str
    updated_at: str
