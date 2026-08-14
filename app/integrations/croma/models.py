from dataclasses import dataclass, field
from typing import Literal


@dataclass
class SourceResult:
    source: str
    status: Literal["ok", "not_found", "error", "skipped"]
    data: dict | None = None
    error: str | None = None
    latency_ms: int = 0
    from_cache: bool = False
