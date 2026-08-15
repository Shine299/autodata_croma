import asyncio
import time
import uuid

from app.integrations.croma.client import CromaClient
from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sbs import map_sbs_soat
from app.integrations.croma.sources.apeseg import merge_insurance_sources
from app.integrations.croma.sources.sutran import map_sutran_infractions
from app.integrations.croma.sources.callao import merge_infractions
from app.integrations.croma.sources.sat_debt import map_sat_tax_debt
from app.integrations.croma.sources.sat_captures import map_sat_capture_order
from app.schemas.common import SourceStatus, SourceSummary
from app.schemas.vehicle import VehicleInspectionResponse

_SOURCES = [
    ("sbs_soat", "/pe/sbs/soat/v1"),
    ("apeseg_soat", "/pe/apeseg/soat/v1"),
    ("sutran", "/pe/sutran/infracciones/v1"),
    ("callao", "/pe/callao/papeletas/v1"),
    ("sat_lima", "/pe/sat-lima/account-status/v1"),
    ("sat_capturas", "/pe/sat-lima/capturas/v1"),
]


def _source_body(source: str, plate: str) -> dict:
    """Body por fuente. SAT Lima cuenta usa document_type/document_number (por placa);
    el resto de fuentes vehiculares reciben `plate` directamente (ver /catalog de Croma)."""
    if source == "sat_lima":
        return {"document_type": "placa", "document_number": plate}
    return {"plate": plate}


async def _fetch_source(client: CromaClient, source: str, path: str, plate: str) -> SourceResult:
    t0 = time.monotonic()
    try:
        result = await client.call(source, path, _source_body(source, plate), cache_key=plate)
        return result
    except Exception as e:
        return SourceResult(
            source=source,
            status="error",
            error=str(e),
            latency_ms=int((time.monotonic() - t0) * 1000),
        )


async def get_vehicle_inspection(plate: str) -> VehicleInspectionResponse:
    # Las 6 fuentes se consultan en paralelo (asyncio.gather). Un AsyncSession de
    # SQLAlchemy NO es seguro para uso concurrente, así que aquí el cliente va SIN
    # sesión (sin caché read-through): consulta Croma directo. La cuota real es amplia
    # (500/24h por endpoint) y la demo rápida usa los fixtures sembrados en fixtures/demo.
    client = CromaClient()
    try:
        results = await asyncio.gather(
            *[_fetch_source(client, src, path, plate) for src, path in _SOURCES],
            return_exceptions=True,
        )

        # Convert exceptions to error SourceResults
        source_results: list[SourceResult] = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                source_results.append(SourceResult(
                    source=_SOURCES[i][0], status="error", error=str(r)
                ))
            else:
                source_results.append(r)

        sbs, apeseg, sutran, callao, sat_debt, sat_captures = source_results

        insurance = merge_insurance_sources(sbs, apeseg)
        infractions = merge_infractions(sutran, callao)
        tax_debt = map_sat_tax_debt(sat_debt)
        capture_order = map_sat_capture_order(sat_captures)

        sources_summary = [
            SourceSummary(
                source=r.source, status=r.status, latency_ms=r.latency_ms, error=r.error
            )
            for r in source_results
        ]

        unverified = [r.source for r in source_results if r.status == "error"]

        any_cache = any(r.from_cache for r in source_results)
        from datetime import datetime, timezone

        return VehicleInspectionResponse(
            inspection_id=f"insp_{uuid.uuid4().hex[:12]}",
            plate=plate,
            created_at=datetime.now(timezone.utc).isoformat(),
            from_cache=any_cache,
            insurance=insurance,
            infractions=infractions,
            tax_debt=tax_debt,
            capture_order=capture_order,
            sources_summary=sources_summary,
            unverified_sources=unverified,
        )
    finally:
        await client.close()
