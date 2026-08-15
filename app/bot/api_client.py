"""D-04 — Cliente HTTP del bot hacia la propia API de AutoData.

El bot corre como proceso aparte (polling); llama a `POST /verifications` por HTTP
según el contrato de `files/03-API-DESIGN.md`. Todo fallo de red o 5xx (p.ej. un 502
por una fuente oficial caída) se convierte en `VerificationApiError`, para que el
handler muestre un mensaje amable en vez de reventar (DoD D-04).

Adapter/boilerplate de errores = delegable (07-AGENTS §Qué SÍ delegar).
"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from app.config import settings


class VerificationApiError(Exception):
    """La API no pudo entregar un veredicto (5xx, timeout o red caída).

    `status_code` es el HTTP recibido, o None si ni siquiera hubo respuesta.
    """

    def __init__(self, message: str, *, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _build_payload(
    plate: str,
    asking_price: Optional[float] = None,
    seller: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Arma el body camelCase de `VerificationRequest` (populate_by_name en la API)."""
    payload: dict[str, Any] = {"plate": plate, "channel": "telegram"}
    if asking_price is not None:
        payload["askingPrice"] = asking_price
    if seller is not None:
        payload["seller"] = seller
    return payload


async def create_verification(
    plate: str,
    asking_price: Optional[float] = None,
    seller: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """POST /verifications (síncrono). Devuelve el objeto `data` del response.

    Lanza `VerificationApiError` ante cualquier problema para que el bot no crashee.
    """
    url = f"{settings.api_base_url}/verifications"
    payload = _build_payload(plate, asking_price, seller)

    try:
        async with httpx.AsyncClient(timeout=settings.croma_timeout_seconds) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:  # timeout, DNS, conexión rechazada, etc.
        raise VerificationApiError(f"no se pudo contactar a la API: {exc}") from exc

    if resp.status_code >= 500:
        raise VerificationApiError(
            f"la API respondió {resp.status_code}", status_code=resp.status_code
        )
    if resp.status_code >= 400:
        # 4xx: error del lado del bot (placa inválida, cuota). No es crash, pero
        # tampoco hay veredicto: lo tratamos como error amable igual.
        raise VerificationApiError(
            f"la API rechazó la consulta ({resp.status_code})",
            status_code=resp.status_code,
        )

    body = resp.json()
    data = body.get("data") if isinstance(body, dict) else None
    if not data:
        raise VerificationApiError("la API devolvió una respuesta vacía")
    return data
