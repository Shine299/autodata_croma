"""Capa de IA de fraseo (Gemini) — solo naturaliza texto, nunca decide.

El veredicto GO/CAUTION/STOP y el precio se calculan con reglas deterministas
(scoring/appraisal). Esta capa solo reescribe texto en un tono peruano cercano sobre
datos que YA existen. Regla de oro: si algo falla (sin key, timeout, error de red, cuota
agotada), `naturalize` devuelve `None` y el bot usa su texto determinista de siempre.

Se usa httpx (ya es dependencia del proyecto) contra el endpoint REST de la API gratuita
de Google AI Studio; sin SDKs pesados.
"""

from __future__ import annotations

import httpx

from app.config import settings

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Salida corta = consumo mínimo de tokens.
_MAX_OUTPUT_TOKENS = 256
_TIMEOUT_SECONDS = 8.0


def is_enabled() -> bool:
    """La IA solo se usa si está habilitada y hay API key configurada."""
    return bool(settings.llm_enabled and settings.gemini_api_key)


async def naturalize(prompt: str, *, system: str | None = None) -> str | None:
    """Pide a Gemini que reescriba/genere un texto corto. Devuelve None ante cualquier fallo.

    `system` (opcional) fija la identidad/tono (p.ej. `SYSTEM_IDENTITY`). El llamador
    SIEMPRE debe tener un fallback determinista para cuando esto devuelva None.
    """
    if not is_enabled():
        return None

    url = _ENDPOINT.format(model=settings.gemini_model)
    payload: dict = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": _MAX_OUTPUT_TOKENS,
        },
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                json=payload,
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return text or None
    except Exception:
        # Falla abierto: nunca rompe el flujo del bot.
        return None
