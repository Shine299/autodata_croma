"""B-08 — Adapter SUTRAN Infracciones.

Mapea la respuesta de Croma SUTRAN a la estructura base del schema `Infractions`.
Calcula la suma total adeudada en PEN y contabiliza las infracciones con clasificación "Muy Grave".
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.vehicle import InfractionItem, Infractions


def _classify_severity(code: str, raw_class: str | None) -> str:
    """Normaliza la clasificación a 'Muy Grave', 'Grave', 'Leve'."""
    if raw_class:
        c = raw_class.strip().upper()
        if "MUY" in c or c == "MG" or c == "M":
            return "Muy Grave"
        if "GRAVE" in c or c == "G":
            return "Grave"
        if "LEVE" in c or c == "L":
            return "Leve"

    # Fallback por código de infracción reglamentario (M*, G*, L*)
    code_upper = (code or "").strip().upper()
    if code_upper.startswith("M"):
        return "Muy Grave"
    if code_upper.startswith("G"):
        return "Grave"
    if code_upper.startswith("L"):
        return "Leve"

    return "Grave"


def map_sutran_infractions(result: SourceResult | dict[str, Any] | None) -> Infractions:
    """Mapea el resultado de la consulta SUTRAN a un schema Infractions."""
    if result is None:
        return Infractions(status="not_found")

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return Infractions(status="error")
        if result.status == "skipped":
            return Infractions(status="skipped")
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return Infractions(status="not_found", has_infractions=False, total=0.0, count=0)

    raw_items = data.get("infractions") or data.get("items") or []
    items: list[InfractionItem] = []
    calculated_total = 0.0
    severe_count = 0

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        doc_num = str(item.get("document_number") or item.get("papeleta") or item.get("code") or "S/N")
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
                source="SUTRAN",
            )
        )

    # Si el payload ya incluye el total consolidado, usarlo si es mayor que la suma individual
    payload_total = float(data.get("total") or 0.0)
    total = max(calculated_total, payload_total)
    count = len(items) if items else int(data.get("count") or 0)
    has_infractions = count > 0 or total > 0

    return Infractions(
        status="ok",
        has_infractions=has_infractions,
        count=count,
        currency="PEN",
        total=round(total, 2),
        severe_count=severe_count,
        items=items,
    )
