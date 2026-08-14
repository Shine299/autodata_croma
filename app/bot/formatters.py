"""D-06 — Formateo del veredicto para Telegram.

Convierte el objeto `data` de `POST /verifications` (contrato de 03-API-DESIGN.md,
Recurso 3, camelCase) en un mensaje Markdown legible en un celular: una sola columna,
sin tablas, con semáforo de emojis y jerarquía visual.

Delegable como "formateo de mensajes de Telegram" (07-AGENTS §Qué SÍ delegar).
El copy final en tono peruano lo cierra P5: los textos aquí son placeholders con la
estructura ya resuelta.
"""

from typing import Any, Dict

# Semáforo del veredicto global.
_VERDICT_EMOJI = {"GO": "🟢", "CAUTION": "🟡", "STOP": "🔴"}
_VERDICT_LABEL = {"GO": "LUZ VERDE", "CAUTION": "CON CUIDADO", "STOP": "ALTO"}

# Emoji por severidad de cada flag.
_SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}


def format_verdict(data: Dict[str, Any]) -> str:
    """Arma el mensaje de veredicto. `data` es el objeto `data` del response de la API."""
    verdict = str(data.get("verdict", "")).upper()
    emoji = _VERDICT_EMOJI.get(verdict, "⚪")
    label = _VERDICT_LABEL.get(verdict, verdict or "SIN VEREDICTO")

    plate = data.get("plate", "?")
    risk = data.get("riskScore")
    headline = data.get("headline", "")
    summary = data.get("summary", "")

    lines: list[str] = []
    # Encabezado: semáforo + etiqueta + placa.
    lines.append(f"{emoji} *{label}* — placa `{plate}`")
    if risk is not None:
        lines.append(f"Riesgo: *{risk}/100*")
    if headline:
        lines.append("")
        lines.append(headline)
    if summary:
        lines.append("")
        lines.append(f"_{summary}_")

    # Flags, uno por línea (sin tabla → sin scroll horizontal).
    flags = data.get("flags") or []
    if flags:
        lines.append("")
        lines.append("*Hallazgos:*")
        for flag in flags:
            sev = str(flag.get("severity", "info")).lower()
            fe = _SEVERITY_EMOJI.get(sev, "•")
            title = flag.get("title", flag.get("code", ""))
            detail = flag.get("detail", "")
            line = f"{fe} *{title}*"
            if detail:
                line += f" — {detail}"
            lines.append(line)

    # Confianza (fuentes verificadas), con aviso si el veredicto quedó limitado.
    conf = data.get("confidence") or {}
    if conf:
        verified = conf.get("verifiedSources", "?")
        total = conf.get("totalSources", "?")
        line = f"Fuentes: {verified}/{total} verificadas"
        if conf.get("capped"):
            line += " ⚠️ (algunas fuentes no respondieron)"
        lines.append("")
        lines.append(line)

    disclaimer = data.get("disclaimer")
    if disclaimer:
        lines.append("")
        lines.append(f"_{disclaimer}_")

    return "\n".join(lines)
