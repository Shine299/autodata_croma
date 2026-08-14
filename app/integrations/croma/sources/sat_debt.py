"""B-10 — Adapter SAT Lima Cuenta (Deuda Tributaria / Vehicular).

Mapea la respuesta de Croma SAT Lima estado de cuenta (por placa) al schema `TaxDebt`.
Extrae los conceptos adeudados (impuesto vehicular, arbitrios/multas asociadas), periodos y montos en PEN.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.vehicle import TaxDebt, TaxDebtItem


def map_sat_tax_debt(result: SourceResult | dict[str, Any] | None) -> TaxDebt:
    """Mapea el resultado de SAT Lima cuenta a un schema TaxDebt."""
    if result is None:
        return TaxDebt(status="not_found", source="SAT_LIMA")

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return TaxDebt(status="error", source="SAT_LIMA")
        if result.status == "skipped":
            return TaxDebt(status="skipped", source="SAT_LIMA")
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return TaxDebt(
            status="not_found",
            has_debt=False,
            total=0.0,
            items=[],
            source="SAT_LIMA",
        )

    raw_items = data.get("items") or data.get("deudas") or data.get("concepts") or []
    items: list[TaxDebtItem] = []
    calculated_total = 0.0

    for item in raw_items:
        if not isinstance(item, dict):
            continue
        concept = str(item.get("concept") or item.get("concepto") or item.get("tributo") or "Impuesto Vehicular")
        period = str(item.get("period") or item.get("periodo") or item.get("anio") or item.get("year") or "N/A")
        amount = float(item.get("amount") or item.get("monto") or item.get("total") or item.get("deuda") or 0.0)
        calculated_total += amount

        items.append(
            TaxDebtItem(
                concept=concept,
                period=period,
                amount=round(amount, 2),
            )
        )

    payload_total = float(data.get("total") or 0.0)
    total = max(calculated_total, payload_total)
    has_debt = bool(data.get("has_debt", total > 0)) or total > 0

    return TaxDebt(
        status="ok",
        has_debt=has_debt,
        currency="PEN",
        total=round(total, 2),
        items=items,
        source="SAT_LIMA",
    )
