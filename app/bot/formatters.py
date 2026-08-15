"""D-06 — Formateo del reporte de compra para Telegram.

Convierte el objeto `data` de `POST /verifications` (contrato de 03-API-DESIGN.md,
camelCase) en un mensaje Markdown honesto y legible en un celular: una sola columna,
sin tablas, con secciones claras.

**Regla de oro (prioridad EXACTITUD > NO INVENTAR):** todo lo que aquí se muestra sale de
datos ya calculados por reglas deterministas (scoring/appraisal) o de lo que respondieron
las fuentes oficiales. Nunca se afirma "verificado" o "limpio" si una fuente no respondió,
y nunca se inventan marca, modelo, año, kilometraje ni precio de mercado (Croma no los da).
"""

from typing import Any, Dict

from app.bot.parsers import format_plate_display

_SEP = "━━━━━━━━━━━━━━━━━━"

# Categorías del vehículo que sí cubre Croma Perú.
_RESPONDED = {"ok", "not_found"}

# Datos que Croma Perú NO provee (requieren SUNARP/MTC, fuera de alcance).
_NO_DISPONIBLE = (
    "Marca, modelo, año, kilometraje, N° de propietarios y precio de mercado"
)


def _status(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ""
    return str(obj.get("status") or "").lower()


def _responded(obj: Any) -> bool:
    """True si la fuente respondió (ok/not_found) o si el fixture no trae status."""
    s = _status(obj)
    return s in _RESPONDED or s == ""


def _unavailable_count(data: Dict[str, Any]) -> int:
    """Cuántas fuentes oficiales no respondieron, según `confidence` (proxy robusto)."""
    conf = data.get("confidence") or {}
    total = conf.get("totalSources")
    verified = conf.get("verifiedSources")
    if isinstance(total, int) and isinstance(verified, int):
        return max(0, total - verified)
    return 0


def _capture_failed(data: Dict[str, Any]) -> bool:
    """True solo si la fuente de orden de captura falló explícitamente (dato crítico)."""
    cap = (data.get("vehicle") or {}).get("captureOrder") or {}
    return _status(cap) in ("error", "skipped")


def purchase_recommendation(data: Dict[str, Any]) -> tuple[str, str, str]:
    """Devuelve (emoji, etiqueta, motivo). 100% determinista.

    🟢 COMPRAR · 🟡 NEGOCIAR · 🔴 NO COMPRAR · ⚪ INFORMACIÓN INSUFICIENTE.
    Nunca fuerza COMPRAR/NO COMPRAR si falta información crítica.
    """
    verdict = str(data.get("verdict", "")).upper()
    unavailable = _unavailable_count(data)

    if verdict == "STOP":
        return ("🔴", "NO COMPRAR", "Se detectó un problema crítico (orden de captura o equivalente).")
    if _capture_failed(data):
        return ("⚪", "INFORMACIÓN INSUFICIENTE",
                "No pude verificar la orden de captura (el dato más importante). No asumo que esté limpio.")
    if unavailable >= 2:
        return ("⚪", "INFORMACIÓN INSUFICIENTE",
                "Varias fuentes oficiales no respondieron. No hay base suficiente para recomendar.")
    if verdict == "CAUTION":
        return ("🟡", "NEGOCIAR",
                "Hay observaciones que justifican pedir descuento o verificar más antes de cerrar.")
    # verdict == GO
    if unavailable == 0:
        return ("🟢", "COMPRAR", "No hallé problemas en las fuentes consultadas y todas respondieron.")
    return ("🟡", "NEGOCIAR",
            "Lo verificado sale bien, pero quedó un dato sin confirmar; verifícalo antes de cerrar.")


def confidence_level(data: Dict[str, Any]) -> tuple[str, str]:
    """Devuelve (emoji, etiqueta) de confianza. Baja si falló una fuente crítica."""
    unavailable = _unavailable_count(data)
    if _capture_failed(data) or unavailable >= 2:
        return ("🔴", "BAJA")
    if unavailable == 1:
        return ("🟡", "MEDIA")
    return ("🟢", "ALTA")


def _verified_and_pending(vehicle: Dict[str, Any]) -> tuple[list[str], list[str]]:
    """Reparte las 4 categorías del vehículo en verificadas vs pendientes (honesto)."""
    verified: list[str] = []
    pending: list[str] = []

    insurance = vehicle.get("insurance") or {}
    infractions = vehicle.get("infractions") or {}
    tax_debt = vehicle.get("taxDebt") or {}
    capture = vehicle.get("captureOrder") or {}

    # SOAT + siniestros (SBS/APESEG)
    if _responded(insurance):
        soat = "vigente" if insurance.get("hasActiveSoat") else "NO vigente"
        verified.append(f"✅ SOAT (SBS/APESEG): {soat}")
        acc = insurance.get("accidentCount") or 0
        verified.append(f"✅ Siniestros SBS (últimos 5 años): {acc}")
    else:
        pending.append("⚠️ SOAT y siniestros: no verificado (la fuente no respondió)")

    # Papeletas (SUTRAN/Callao)
    if _responded(infractions):
        total = infractions.get("total") or 0
        count = infractions.get("count") or 0
        severe = infractions.get("severeCount") or 0
        if total or count:
            verified.append(f"✅ Papeletas (SUTRAN/Callao): S/ {total:,.0f} en {count} ({severe} graves)")
        else:
            verified.append("✅ Papeletas (SUTRAN/Callao): sin papeletas")
    else:
        pending.append("⚠️ Papeletas: no verificado (la fuente no respondió)")

    # Deuda tributaria (SAT Lima)
    if _responded(tax_debt):
        total = tax_debt.get("total") or 0
        verified.append(
            f"✅ Deuda SAT Lima: S/ {total:,.0f}" if total else "✅ Deuda SAT Lima: sin deuda"
        )
    else:
        pending.append("⚠️ Deuda tributaria: no verificado (la fuente no respondió)")

    # Orden de captura (SAT Lima) — el dato killer
    if _responded(capture):
        if capture.get("hasCaptureOrder"):
            verified.append("🔴 Orden de captura (SAT): VIGENTE")
        else:
            verified.append("✅ Orden de captura (SAT): sin orden")
    else:
        pending.append("⚠️ Orden de captura: NO verificado (la fuente no respondió) — dato crítico")

    return verified, pending


def _seller_lines(seller: Dict[str, Any]) -> list[str]:
    lines: list[str] = []
    taxpayer = seller.get("taxpayer") or {}
    debt = seller.get("personalDebt") or {}
    if _responded(taxpayer):
        if taxpayer.get("isVehicleTrader"):
            lines.append("⚠️ Vendedor: figura con actividad comercial de venta de vehículos (SUNAT)")
        elif taxpayer.get("found"):
            lines.append("✅ Vendedor: registrado en SUNAT, sin actividad de revendedor")
        else:
            lines.append("✅ Vendedor: sin registros de actividad comercial vehicular")
    else:
        lines.append("⚠️ Vendedor (SUNAT): no verificado (la fuente no respondió)")
    if _responded(debt):
        total = debt.get("total") or 0
        if total:
            lines.append(f"⚠️ Vendedor: deuda personal en SAT de S/ {total:,.0f}")
    return lines


def _price_lines(data: Dict[str, Any]) -> list[str]:
    """Sección de análisis de precio. Objetivo = pedido − deducciones VERIFICADAS."""
    appraisal = data.get("appraisal")
    if not appraisal:
        return [
            "💰 *ANÁLISIS DEL PRECIO*",
            "",
            "Aún no me diste el precio. Mándame a cuánto te lo ofrecen (ej. `29 mil`) y",
            "calculo el precio objetivo de negociación.",
        ]

    asking = appraisal.get("askingPrice") or 0
    fair = appraisal.get("fairPrice") or 0
    deductions = appraisal.get("deductions") or []

    lines = ["💰 *ANÁLISIS DEL PRECIO*", "", f"Precio solicitado: *S/ {asking:,.0f}*", ""]

    # Caso killer: con orden de captura no corresponde negociar ningún precio.
    if appraisal.get("recommendation") == "NO_COMPRAR" or (asking > 0 and fair == 0):
        lines.append("🔴 No corresponde negociar precio: el vehículo tiene un problema que")
        lines.append("desaconseja la compra por completo (ver recomendación abajo).")
        return lines

    if deductions:
        lines.append("Deducciones *verificadas* (costos reales a tu cargo):")
        for d in deductions:
            lines.append(f"• {d.get('concept')}: *-S/ {d.get('amount', 0):,.0f}*")
        lines.append("")
        lines.append(f"🎯 Precio objetivo de negociación: *S/ {fair:,.0f}*")
    else:
        lines.append("No hallé deudas ni cargas verificadas para descontar del precio.")
        lines.append(f"🎯 En la parte verificable, el objetivo se mantiene en *S/ {asking:,.0f}*.")
    lines.append("")
    lines.append("_No es una tasación oficial y no incluye precio de mercado (Croma no lo provee)._")
    return lines


def format_verdict(data: Dict[str, Any]) -> str:
    """Arma el reporte de compra. `data` es el objeto `data` del response de la API."""
    vehicle = data.get("vehicle") or {}
    plate = format_plate_display(data.get("plate"))
    rec_emoji, rec_label, rec_reason = purchase_recommendation(data)
    conf_emoji, conf_label = confidence_level(data)
    unavailable = _unavailable_count(data)
    verdict = str(data.get("verdict", "")).upper()

    lines: list[str] = []
    lines.append("🚗 *EVALUACIÓN DEL VEHÍCULO*")
    lines.append("")
    lines.append(f"Placa: *{plate}*")

    # Título del scoring solo si es honesto mostrarlo (no cuando GO con fuentes pendientes).
    headline = data.get("headline")
    if headline and not (verdict == "GO" and unavailable > 0):
        lines.append(f"_{headline}_")

    verified, pending = _verified_and_pending(vehicle)
    seller = data.get("seller")
    if seller:
        verified_seller = _seller_lines(seller)
    else:
        verified_seller = []

    lines.append("")
    lines.append(_SEP)
    lines.append("📋 *INFORMACIÓN VERIFICADA*")
    lines.append("")
    for ln in verified + verified_seller:
        lines.append(ln)

    if pending:
        lines.append("")
        lines.append(_SEP)
        lines.append("⚠️ *INFORMACIÓN PENDIENTE (no verificada)*")
        lines.append("")
        for ln in pending:
            lines.append(ln)

    # Datos que Croma no provee — siempre explícitos, nunca inventados.
    lines.append("")
    lines.append(_SEP)
    lines.append("➖ *NO DISPONIBLE*")
    lines.append("")
    lines.append(f"{_NO_DISPONIBLE}: no disponibles (requieren SUNARP/MTC, fuera de alcance).")

    # Análisis de precio.
    lines.append("")
    lines.append(_SEP)
    for ln in _price_lines(data):
        lines.append(ln)

    # Riesgos (de las flags del scoring).
    flags = data.get("flags") or []
    lines.append("")
    lines.append(_SEP)
    lines.append("⚠️ *RIESGOS*")
    lines.append("")
    if flags:
        for flag in flags:
            title = flag.get("title", flag.get("code", ""))
            detail = flag.get("detail", "")
            lines.append(f"• *{title}*" + (f" — {detail}" if detail else ""))
    elif pending:
        lines.append("• Quedaron datos sin verificar (ver sección de arriba).")
    else:
        lines.append("• Sin riesgos detectados en las fuentes consultadas.")

    # Recomendación + confianza.
    lines.append("")
    lines.append(_SEP)
    lines.append("🧠 *RECOMENDACIÓN*")
    lines.append("")
    lines.append(f"{rec_emoji} *{rec_label}*")
    lines.append(rec_reason)
    lines.append("")

    conf = data.get("confidence") or {}
    verified_n = conf.get("verifiedSources", "?")
    total_n = conf.get("totalSources", "?")
    lines.append(f"📊 Confianza: {conf_emoji} *{conf_label}*  (fuentes {verified_n}/{total_n})")
    if unavailable > 0 or conf.get("capped"):
        lines.append("⚠️ Algunas fuentes no respondieron; no asumo los datos faltantes.")

    lines.append("")
    lines.append(_SEP)
    lines.append("_Esto es apoyo para tu decisión, no una garantía. Antes de pagar, verifica_")
    lines.append("_la documentación y haz una inspección mecánica presencial._")

    return "\n".join(lines)


_SOURCE_LABELS = {
    "sbs_soat": "SBS (SOAT/siniestros)",
    "apeseg_soat": "APESEG (SOAT)",
    "sutran": "SUTRAN (papeletas)",
    "callao": "Callao (papeletas)",
    "sat_lima": "SAT Lima (deuda)",
    "sat_capturas": "SAT Lima (captura)",
    "SUNAT": "SUNAT (vendedor)",
    "SAT_LIMA": "SAT Lima (vendedor)",
}

_STATUS_LABELS = {
    "ok": "✅ respondió",
    "not_found": "✅ sin registros",
    "error": "❌ no respondió",
    "skipped": "➖ no consultada",
}


def format_detail(data: Dict[str, Any]) -> str:
    """Desglose completo de una verificación (botón 'Ver detalle')."""
    vehicle = data.get("vehicle") or {}
    plate = format_plate_display(data.get("plate"))
    lines = [f"🔍 *DETALLE — placa {plate}*", ""]

    # Seguro / SOAT
    ins = vehicle.get("insurance") or {}
    if _responded(ins):
        lines.append("*Seguro (SBS/APESEG)*")
        lines.append(f"• SOAT: {'vigente' if ins.get('hasActiveSoat') else 'NO vigente'}")
        if ins.get("company"):
            lines.append(f"• Aseguradora: {ins.get('company')}")
        if ins.get("endDate"):
            lines.append(f"• Vence: {ins.get('endDate')}")
        lines.append(f"• Siniestros (5 años): {ins.get('accidentCount', 0)}")
        if ins.get("policyCount"):
            lines.append(f"• Pólizas registradas: {ins.get('policyCount')}")
        lines.append("")

    # Papeletas
    inf = vehicle.get("infractions") or {}
    if _responded(inf):
        lines.append("*Papeletas (SUTRAN/Callao)*")
        lines.append(f"• Total: S/ {inf.get('total', 0):,.0f} en {inf.get('count', 0)} papeleta(s), "
                     f"{inf.get('severeCount', 0)} grave(s)")
        for it in (inf.get("items") or [])[:8]:
            code = it.get("infractionCode", "?")
            cls = it.get("classification", "")
            src = it.get("source", "")
            lines.append(f"   – {code} {cls} ({src})".rstrip())
        lines.append("")

    # Deuda SAT
    debt = vehicle.get("taxDebt") or {}
    if _responded(debt):
        lines.append("*Deuda tributaria (SAT Lima)*")
        lines.append(f"• Total: S/ {debt.get('total', 0):,.0f}")
        for it in (debt.get("items") or [])[:8]:
            lines.append(f"   – {it.get('concept', '?')} {it.get('period', '')}: "
                         f"S/ {it.get('amount', 0):,.0f}".rstrip())
        lines.append("")

    # Orden de captura
    cap = vehicle.get("captureOrder") or {}
    if _responded(cap):
        lines.append("*Orden de captura (SAT Lima)*")
        if cap.get("hasCaptureOrder"):
            lines.append(f"• 🔴 VIGENTE" + (f" — {cap.get('reason')}" if cap.get("reason") else ""))
        else:
            lines.append("• Sin orden de captura")
        lines.append("")

    # Vendedor
    seller = data.get("seller")
    if seller:
        tp = seller.get("taxpayer") or {}
        pd = seller.get("personalDebt") or {}
        lines.append("*Vendedor (SUNAT/SAT)*")
        if tp.get("name"):
            lines.append(f"• {tp.get('name')}")
        lines.append(f"• Revendedor de autos: {'sí' if tp.get('isVehicleTrader') else 'no'}")
        if pd.get("total"):
            lines.append(f"• Deuda personal: S/ {pd.get('total', 0):,.0f}")
        lines.append("")

    # Estado de las fuentes
    summ = vehicle.get("sourcesSummary") or []
    if seller:
        summ = summ + (seller.get("sourcesSummary") or [])
    if summ:
        lines.append("*Estado de las fuentes*")
        for s in summ:
            name = _SOURCE_LABELS.get(s.get("source"), s.get("source", "?"))
            st = _STATUS_LABELS.get(str(s.get("status", "")).lower(), s.get("status", ""))
            lat = s.get("latencyMs")
            lines.append(f"• {name}: {st}" + (f" ({lat} ms)" if lat else ""))
        lines.append("")

    vid = data.get("verificationId", "")
    if vid:
        lines.append(f"_ID de consulta: {vid}_")
    return "\n".join(lines).strip()


def format_appraisal(data: Dict[str, Any]) -> str:
    """Formatea la tasación cuando se pide de forma independiente (botón 💰)."""
    asking_price = data.get("askingPrice", 0)
    fair_price = data.get("fairPrice", 0)

    lines = [
        f"💰 *Precio solicitado:* S/ {asking_price:,.0f}",
        f"🎯 *Precio objetivo (pedido − deducciones verificadas):* S/ {fair_price:,.0f}",
        "",
    ]

    deductions = data.get("deductions", [])
    if deductions:
        lines.append("*Deducciones verificadas:*")
        for ded in deductions:
            lines.append(f"• {ded.get('concept')}: *-S/ {ded.get('amount', 0):,.0f}*")
        lines.append("")
    else:
        lines.append("_No hallé deudas ni cargas verificadas para descontar._")
        lines.append("")

    script = data.get("negotiationScript", "")
    if script:
        lines.append("*Guion de negociación sugerido:*")
        lines.append(f"```\n{script}\n```")

    lines.append("")
    lines.append("_No es una tasación oficial y no incluye precio de mercado (Croma no lo provee)._")
    return "\n".join(lines)
