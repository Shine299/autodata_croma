"""B-13 — Adapter SAT Lima por DNI/RUC (Deuda Personal / Vendedor).

Mapea la respuesta de Croma SAT Lima por documento al schema `PersonalDebt`.
Extrae deuda personal, total en PEN, cantidad de deudas y placas relacionadas vinculadas al titular.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.seller import PersonalDebt


def map_sat_seller_debt(result: SourceResult | dict[str, Any] | None) -> PersonalDebt:
    """Mapea el resultado de SAT Lima por documento a un schema PersonalDebt."""
    if result is None:
        return PersonalDebt(status=SourceStatus.NOT_FOUND, has_debt=False, source="SAT_LIMA")

    if isinstance(result, SourceResult):
        if result.status == "error":
            return PersonalDebt(status=SourceStatus.ERROR, has_debt=False, source="SAT_LIMA")
        if result.status == "skipped":
            return PersonalDebt(status=SourceStatus.SKIPPED, has_debt=False, source="SAT_LIMA")
        data = result.data or {}
        status = SourceStatus.OK if (result.status == "ok" and data.get("found", True)) else SourceStatus.NOT_FOUND
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = SourceStatus.OK if found else SourceStatus.NOT_FOUND

    if not data or status == SourceStatus.NOT_FOUND or not data.get("found", True):
        return PersonalDebt(
            status=SourceStatus.NOT_FOUND,
            has_debt=False,
            total=0.0,
            item_count=0,
            related_plates=[],
            source="SAT_LIMA",
        )

    # Extraer total de deuda
    total = float(data.get("total") or data.get("monto_total") or data.get("deuda_total") or 0.0)

    # Extraer items o deudas detalladas
    raw_items = data.get("items") or data.get("deudas") or data.get("conceptos") or []
    item_count = int(data.get("item_count") or data.get("cantidad_deudas") or len(raw_items) or 0)

    # Extraer placas relacionadas
    raw_plates = data.get("related_plates") or data.get("placas_relacionadas") or data.get("placas") or []
    related_plates = [str(p).strip().upper() for p in raw_plates if p]

    has_debt = bool(data.get("has_debt", total > 0 or item_count > 0)) or total > 0

    return PersonalDebt(
        status=SourceStatus.OK,
        has_debt=has_debt,
        currency="PEN",
        total=round(total, 2),
        item_count=item_count,
        related_plates=related_plates,
        source="SAT_LIMA",
    )
