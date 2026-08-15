from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.integrations.croma.client import CromaClient
from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.apeseg import merge_insurance_sources
from app.integrations.croma.sources.callao import merge_infractions
from app.integrations.croma.sources.sat_captures import map_sat_capture_order
from app.integrations.croma.sources.sat_debt import map_sat_tax_debt
from app.schemas.common import SourceStatus, SourceSummary
from app.schemas.vehicle import CaptureOrder, Infractions, Insurance, TaxDebt
from app.services.plate import normalize_plate


@dataclass
class SourceSpec:
    key: str
    display: str
    path: str


ALL_SOURCES = [
    SourceSpec("sbs_soat", "SBS", "/pe/sbs/soat"),
    SourceSpec("apeseg_soat", "APESEG", "/pe/apeseg/soat"),
    SourceSpec("sutran", "SUTRAN", "/pe/sutran/infracciones"),
    SourceSpec("callao", "Callao", "/pe/callao/papeletas"),
    SourceSpec("sat_lima", "SAT Lima", "/pe/sat-lima/cuenta"),
    SourceSpec("sat_capturas", "SAT Capturas", "/pe/sat-lima/capturas"),
]

_KEY_INDEX = {s.key: s for s in ALL_SOURCES}


@dataclass
class OrchestratorResult:
    insurance: Insurance
    infractions: Infractions
    tax_debt: TaxDebt
    capture_order: CaptureOrder
    sources_summary: list[SourceSummary] = field(default_factory=list)
    unverified_sources: list[str] = field(default_factory=list)
    total_latency_ms: int = 0


async def fetch_all_sources(
    client: CromaClient,
    plate: str,
    *,
    sources: list[str] | None = None,
) -> OrchestratorResult:
    plate = normalize_plate(plate)

    specs = ALL_SOURCES
    if sources is not None:
        allowed = {s.lower() for s in sources}
        specs = [s for s in ALL_SOURCES if s.key in allowed or s.display.lower() in allowed]

    active_keys = {s.key for s in specs}
    coros = {
        s.key: client.call(s.key, s.path, {"plate": plate}, cache_key=plate)
        for s in specs
    }

    start = time.monotonic()
    raw: dict[str, SourceResult] = {}
    results = await asyncio.gather(*coros.values(), return_exceptions=True)
    for key, result in zip(coros.keys(), results):
        if isinstance(result, Exception):
            raw[key] = SourceResult(source=key, status="error", error=str(result))
        else:
            raw[key] = result
    total_latency_ms = int((time.monotonic() - start) * 1000)

    for s in ALL_SOURCES:
        if s.key not in active_keys:
            raw[s.key] = SourceResult(source=s.key, status="skipped")

    insurance = merge_insurance_sources(
        raw.get("sbs_soat"),
        raw.get("apeseg_soat"),
    )
    infractions = merge_infractions(
        raw.get("sutran"),
        raw.get("callao"),
    )
    tax_debt = map_sat_tax_debt(raw.get("sat_lima"))
    capture_order = map_sat_capture_order(raw.get("sat_capturas"))

    summaries: list[SourceSummary] = []
    unverified: list[str] = []
    for s in ALL_SOURCES:
        r = raw[s.key]
        summaries.append(SourceSummary(
            source=s.display,
            status=SourceStatus(r.status),
            latency_ms=r.latency_ms,
            error=r.error,
        ))
        if r.status != "ok":
            unverified.append(s.display)

    return OrchestratorResult(
        insurance=insurance,
        infractions=infractions,
        tax_debt=tax_debt,
        capture_order=capture_order,
        sources_summary=summaries,
        unverified_sources=unverified,
        total_latency_ms=total_latency_ms,
    )
