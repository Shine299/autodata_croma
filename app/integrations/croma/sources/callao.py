"""B-09 — Adapter Callao Papeletas + Merge con SUTRAN.

Mapea las papeletas de la Municipalidad Provincial del Callao y las consolida
junto con las infracciones de SUTRAN en el schema unificado `Infractions`.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.integrations.croma.sources.sutran import _classify_severity, map_sutran_infractions
from app.schemas.common import SourceStatus
from app.schemas.vehicle import InfractionItem, Infractions


def map_callao_infractions(
    result: SourceResult | dict[str, Any] | None,
) -> tuple[SourceStatus, list[InfractionItem], float, int]:
    """Extrae las infracciones del Callao.

    Returns:
        tuple: (status, items, total_amount, severe_count)
    """
    if result is None:
        return "not_found", [], 0.0, 0

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return "error", [], 0.0, 0
        if result.status == "skipped":
            return "skipped", [], 0.0, 0
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return "not_found", [], 0.0, 0

    raw_items = data.get("papeletas") or data.get("infractions") or data.get("items") or []
    items: list[InfractionItem] = []
    calculated_total = 0.0
    severe_count = 0

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        doc_num = str(item.get("document_number") or item.get("papeleta") or item.get("numero") or "S/N")
        doc_type = str(item.get("document_type") or item.get("tipo") or "PAPELETA")
        doc_date = item.get("document_date") or item.get("fecha") or item.get("date")
        code = str(item.get("infraction_code") or item.get("codigo") or item.get("code") or "")
        raw_classification = item.get("classification") or item.get("gravedad") or item.get("severity")
        classification = _classify_severity(code, raw_classification)

        if classification == "Muy Grave":
            severe_count += 1

        amount = float(item.get("amount") or item.get("monto") or item.get("debt") or 0.0)
        calculated_total += amount

        items.append(
            InfractionItem(
                document_number=doc_num,
                document_type=doc_type,
                document_date=str(doc_date) if doc_date else None,
                infraction_code=code,
                classification=classification,
                source="CALLAO",
            )
        )

    payload_total = float(data.get("total") or 0.0)
    total = max(calculated_total, payload_total)

    return "ok", items, total, severe_count


def merge_infractions(
    sutran_result: SourceResult | dict[str, Any] | Infractions | None,
    callao_result: SourceResult | dict[str, Any] | None,
) -> Infractions:
    """Consolida las infracciones de SUTRAN (nacionales) y Callao (provinciales)."""
    # 1. Base SUTRAN
    if isinstance(sutran_result, Infractions):
        sutran = sutran_result
    else:
        sutran = map_sutran_infractions(sutran_result)

    # 2. Extraer Callao
    callao_status, callao_items, callao_total, callao_severe = map_callao_infractions(callao_result)

    # 3. Determinar status consolidado
    sutran_status = sutran.status
    if sutran_status == "error" and callao_status == "error":
        final_status: SourceStatus = "error"
    elif sutran_status == "ok" or callao_status == "ok":
        final_status = "ok"
    elif sutran_status == "not_found" and callao_status == "not_found":
        final_status = "not_found"
    elif sutran_status == "skipped" and callao_status == "skipped":
        final_status = "skipped"
    else:
        final_status = "ok" if (sutran_status == "ok" or callao_status == "ok") else "not_found"

    # 4. Consolidar items y totales
    consolidated_items = list(sutran.items) + callao_items
    total_amount = round(sutran.total + callao_total, 2)
    total_count = len(consolidated_items)
    severe_count = sutran.severe_count + callao_severe
    has_infractions = total_count > 0 or total_amount > 0

    return Infractions(
        status=final_status,
        has_infractions=has_infractions,
        count=total_count,
        currency="PEN",
        total=total_amount,
        severe_count=severe_count,
        items=consolidated_items,
    )
