"""B-07 — Adapter APESEG SOAT + Merge con SBS.

Mapea la respuesta de Croma APESEG SOAT (certificados y vigencia actual) y
fusiona los datos con la siniestralidad histórica de SBS en un schema `Insurance` consolidado.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sbs import map_sbs_soat
from app.schemas.common import SourceStatus
from app.schemas.vehicle import Insurance


def map_apeseg_soat(result: SourceResult | dict[str, Any] | None) -> dict[str, Any]:
    """Extrae y normaliza los datos de APESEG SOAT."""
    if result is None:
        return {"status": "not_found", "has_active_soat": False}

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return {"status": "error", "has_active_soat": False}
        if result.status == "skipped":
            return {"status": "skipped", "has_active_soat": False}
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return {"status": "not_found", "has_active_soat": False, "certificates_count": 0}

    has_active = bool(data.get("has_active_soat", False))
    active = data.get("active") or {}
    certificates = data.get("certificates") or []
    count = int(data.get("count") or (len(certificates) if isinstance(certificates, list) else 0))

    company = active.get("company") if isinstance(active, dict) else None
    policy_number = active.get("policy_number") if isinstance(active, dict) else None
    start_date = active.get("start_date") if isinstance(active, dict) else None
    end_date = active.get("end_date") if isinstance(active, dict) else None
    active_status = active.get("status") if isinstance(active, dict) else None

    # Si el estado explícito es VIGENTE, asegurar has_active = True
    if active_status and str(active_status).upper() == "VIGENTE":
        has_active = True

    return {
        "status": "ok",
        "has_active_soat": has_active,
        "company": company,
        "policy_number": policy_number,
        "start_date": start_date,
        "end_date": end_date,
        "certificates_count": count,
    }


def merge_insurance_sources(
    sbs_result: SourceResult | dict[str, Any] | Insurance | None,
    apeseg_result: SourceResult | dict[str, Any] | None,
) -> Insurance:
    """Combina los resultados de SBS (siniestralidad) y APESEG (vigencia actual de póliza)."""
    # 1. Obtener base de SBS
    if isinstance(sbs_result, Insurance):
        sbs_insurance = sbs_result
    else:
        sbs_insurance = map_sbs_soat(sbs_result)

    # 2. Extraer datos de APESEG
    apeseg_data = map_apeseg_soat(apeseg_result)

    # 3. Determinar status global de Insurance
    sbs_status = sbs_insurance.status
    apeseg_status = apeseg_data.get("status", "not_found")

    if sbs_status == "error" and apeseg_status == "error":
        final_status: SourceStatus = "error"
    elif sbs_status == "ok" or apeseg_status == "ok":
        final_status = "ok"
    elif sbs_status == "not_found" and apeseg_status == "not_found":
        final_status = "not_found"
    elif sbs_status == "skipped" and apeseg_status == "skipped":
        final_status = "skipped"
    else:
        # Una falló y otra no fue encontrada o viceversa
        final_status = "ok" if (sbs_status == "ok" or apeseg_status == "ok") else "not_found"

    # 4. Fusionar campos
    # Siniestralidad y data_through provienen de SBS
    accident_count = sbs_insurance.accident_count
    data_through = sbs_insurance.data_through

    # Vigencia activa: APESEG tiene prioridad para póliza vigente actual
    if apeseg_data.get("has_active_soat"):
        has_active_soat = True
        company = apeseg_data.get("company") or sbs_insurance.company
        policy_number = apeseg_data.get("policy_number") or sbs_insurance.policy_number
        start_date = apeseg_data.get("start_date") or sbs_insurance.start_date
        end_date = apeseg_data.get("end_date") or sbs_insurance.end_date
    else:
        has_active_soat = sbs_insurance.has_active_soat
        company = sbs_insurance.company or apeseg_data.get("company")
        policy_number = sbs_insurance.policy_number or apeseg_data.get("policy_number")
        start_date = sbs_insurance.start_date or apeseg_data.get("start_date")
        end_date = sbs_insurance.end_date or apeseg_data.get("end_date")

    policy_count = max(
        sbs_insurance.policy_count,
        apeseg_data.get("certificates_count", 0),
    )

    return Insurance(
        status=final_status,
        has_active_soat=has_active_soat,
        company=company,
        policy_number=policy_number,
        start_date=start_date,
        end_date=end_date,
        accident_count=accident_count,
        policy_count=policy_count,
        data_through=data_through,
        source="SBS + APESEG",
    )
