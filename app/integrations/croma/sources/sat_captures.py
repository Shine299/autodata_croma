"""B-11 — Adapter SAT Lima Capturas (Orden de Captura / Internamiento).

Mapea la respuesta de Croma SAT Lima capturas al schema `CaptureOrder`.
Extrae la presencia de órdenes de captura vigentes, fecha de emisión y motivo de embargo/depósito.
"""

from __future__ import annotations

from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.vehicle import CaptureOrder


def map_sat_capture_order(result: SourceResult | dict[str, Any] | None) -> CaptureOrder:
    """Mapea el resultado de SAT Lima capturas a un schema CaptureOrder."""
    if result is None:
        return CaptureOrder(status="not_found", source="SAT_LIMA")

    if isinstance(result, SourceResult):
        status: SourceStatus = result.status
        data = result.data or {}
        if result.status == "error":
            return CaptureOrder(status="error", source="SAT_LIMA")
        if result.status == "skipped":
            return CaptureOrder(status="skipped", source="SAT_LIMA")
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = "ok" if found else "not_found"

    if not data or status == "not_found":
        return CaptureOrder(
            status="not_found",
            has_capture_order=False,
            issued_at=None,
            reason=None,
            source="SAT_LIMA",
        )

    has_capture = bool(
        data.get("has_capture_order")
        or data.get("has_capture")
        or data.get("tiene_captura")
        or data.get("orden_captura", False)
    )

    issued_at = (
        data.get("issued_at")
        or data.get("fecha_emision")
        or data.get("fecha")
        or data.get("issued_date")
    )
    reason = (
        data.get("reason")
        or data.get("motivo")
        or data.get("causal")
        or data.get("description")
    )

    # Si hay orden de captura pero no venía boolean explícito
    captures_list = data.get("captures") or data.get("ordenes")
    if isinstance(captures_list, list) and len(captures_list) > 0:
        has_capture = True
        first = captures_list[0]
        if isinstance(first, dict):
            issued_at = issued_at or first.get("issued_at") or first.get("fecha")
            reason = reason or first.get("reason") or first.get("motivo")

    return CaptureOrder(
        status="ok",
        has_capture_order=has_capture,
        issued_at=str(issued_at) if issued_at else None,
        reason=str(reason) if reason else None,
        source="SAT_LIMA",
    )
