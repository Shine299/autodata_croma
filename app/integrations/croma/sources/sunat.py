"""B-12 — Adapter SUNAT por documento (DNI / RUC).

Mapea la respuesta de Croma SUNAT (ficha de contribuyente) al schema `Taxpayer`.
Detecta si la actividad económica corresponde a la venta/comercialización de vehículos
(is_vehicle_trader = True).
"""

from __future__ import annotations

import re
from typing import Any

from app.integrations.croma.models import SourceResult
from app.schemas.common import SourceStatus
from app.schemas.seller import Taxpayer

VEHICLE_TRADING_KEYWORDS = [
    r"VENTA.*VEHICUL",
    r"COMERCIO.*VEHICUL",
    r"AUTOMOTOR",
    r"AUTOMOVIL",
    r"4510",  # CIIU Venta de vehículos automotores
    r"4520",  # Mantenimiento y reparación
    r"4530",  # Venta de partes y piezas
    r"4540",  # Venta de motocicletas
    r"CONCESIONARI",
    r"COMPRA.*VENTA.*AUTO",
]

COMPILED_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in VEHICLE_TRADING_KEYWORDS]


def is_vehicle_trader_activity(activity_text: str | None, raw_data: dict[str, Any] | None = None) -> bool:
    """Evalúa si el texto de la actividad económica o campos relacionados indican venta de autos."""
    if raw_data:
        if raw_data.get("is_vehicle_trader") is True or raw_data.get("isVehicleTrader") is True:
            return True
        # Check secondary activities if any
        sec_activities = raw_data.get("secondary_activities") or raw_data.get("actividades_secundarias") or []
        for sec in sec_activities:
            if any(p.search(str(sec)) for p in COMPILED_PATTERNS):
                return True

    if not activity_text:
        return False

    return any(p.search(activity_text) for p in COMPILED_PATTERNS)


def map_sunat_taxpayer(result: SourceResult | dict[str, Any] | None) -> Taxpayer:
    """Mapea el resultado de SUNAT a un schema Taxpayer."""
    if result is None:
        return Taxpayer(status=SourceStatus.NOT_FOUND, found=False, source="SUNAT")

    if isinstance(result, SourceResult):
        if result.status == "error":
            return Taxpayer(status=SourceStatus.ERROR, found=False, source="SUNAT")
        if result.status == "skipped":
            return Taxpayer(status=SourceStatus.SKIPPED, found=False, source="SUNAT")
        data = result.data or {}
        status = SourceStatus.OK if (result.status == "ok" and data.get("found", True)) else SourceStatus.NOT_FOUND
    else:
        data = result
        found = data.get("found", True) if isinstance(data, dict) else False
        status = SourceStatus.OK if found else SourceStatus.NOT_FOUND

    if not data or status == SourceStatus.NOT_FOUND or not data.get("found", True):
        return Taxpayer(
            status=SourceStatus.NOT_FOUND,
            found=False,
            source="SUNAT",
        )

    name = data.get("name") or data.get("razon_social") or data.get("nombre") or data.get("nombre_completo")
    ruc = str(data.get("ruc") or data.get("numero_documento") or data.get("document_number") or "") or None
    taxpayer_status = data.get("taxpayer_status") or data.get("estado") or data.get("estado_contribuyente")
    condition = data.get("condition") or data.get("condicion") or data.get("condicion_domicilio")
    main_activity = (
        data.get("main_activity")
        or data.get("actividad_economica")
        or data.get("actividad_principal")
        or data.get("ciiu")
    )
    registered_at = data.get("registered_at") or data.get("fecha_inscripcion") or data.get("fecha_registro")

    is_trader = is_vehicle_trader_activity(main_activity, data)

    return Taxpayer(
        status=SourceStatus.OK,
        found=True,
        name=name,
        ruc=ruc,
        taxpayer_status=taxpayer_status,
        condition=condition,
        main_activity=main_activity,
        is_vehicle_trader=is_trader,
        registered_at=registered_at,
        source="SUNAT",
    )
