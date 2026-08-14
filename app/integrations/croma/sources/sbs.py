"""B-06 — Adapter SBS SOAT.

Mapea la respuesta de Croma SBS SOAT a la estructura base del schema `Insurance`.
Extrae siniestralidad (accidentes en los últimos 5 años), historial de pólizas y data_through.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.vehicle import Insurance


def map_sbs_soat(result: SourceResult | dict[str, Any] | None) -> Insurance:
    """Mapea el resultado de la consulta SBS a un schema Insurance."""
    if result is None:
        return Insurance(status="not_found", source="SBS")

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return Insurance(status="error", source="SBS")
        if result.status == "skipped":
            return Insurance(status="skipped", source="SBS")
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return Insurance(
            status="not_found",
            has_active_soat=False,
            accident_count=0,
            policy_count=0,
            source="SBS",
        )

    # Extraer campos de SBS
    accident_count = int(data.get("accident_count") or 0)
    policies = data.get("policies") or []
    policy_count = int(data.get("count") or (len(policies) if isinstance(policies, list) else 0))
    data_through = data.get("data_through")
    has_active_soat = bool(data.get("has_active_soat", False))

    active = data.get("active") or {}
    company = active.get("company") if isinstance(active, dict) else None
    policy_number = active.get("policy_number") if isinstance(active, dict) else None
    start_date = active.get("start_date") if isinstance(active, dict) else None
    end_date = active.get("end_date") if isinstance(active, dict) else None

    return Insurance(
        status="ok",
        has_active_soat=has_active_soat,
        company=company,
        policy_number=policy_number,
        start_date=start_date,
        end_date=end_date,
        accident_count=accident_count,
        policy_count=policy_count,
        data_through=data_through,
        source="SBS",
    )
