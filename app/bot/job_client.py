"""D-05 — Cliente del modo asíncrono: arranca el job y lo pollea.

Sobre el path async de C-09 (`Prefer: respond-async` → `GET /jobs/{id}`), este cliente
permite al bot mostrar mensajes progresivos: dispara un callback por cada fuente nueva
que se completa, y al final devuelve el objeto `data` del veredicto.

Adapter de polling = delegable (07-AGENTS §Qué SÍ delegar).
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

import httpx

from app.bot.api_client import VerificationApiError, _build_payload
from app.config import settings

OnSourceDone = Callable[[str], Awaitable[None]]


async def start_async_verification(
    plate: str,
    asking_price: Optional[float] = None,
    seller: Optional[dict[str, Any]] = None,
) -> str:
    """POST /verifications con `Prefer: respond-async`. Devuelve el `jobId`."""
    url = f"{settings.api_base_url}/verifications"
    payload = _build_payload(plate, asking_price, seller)

    try:
        async with httpx.AsyncClient(timeout=settings.croma_timeout_seconds) as client:
            resp = await client.post(
                url, json=payload, headers={"Prefer": "respond-async"}
            )
    except httpx.RequestError as exc:
        raise VerificationApiError(
            f"no se pudo contactar a la API: {exc}", connection_error=True
        ) from exc

    if resp.status_code >= 400:
        raise VerificationApiError(
            f"la API no aceptó el job ({resp.status_code})",
            status_code=resp.status_code,
        )

    data = (resp.json() or {}).get("data") or {}
    job_id = data.get("jobId")
    if not job_id:
        raise VerificationApiError("la API no devolvió jobId")
    return job_id


async def poll_job(
    job_id: str,
    on_source_done: Optional[OnSourceDone] = None,
    *,
    interval: float = 0.5,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Pollea `GET /jobs/{id}` hasta `completed`/`failed`.

    Llama `on_source_done(source)` una vez por cada fuente nueva que aparece completada
    (en orden), lo que da los mensajes secuenciales de D-05. Devuelve el objeto `data`
    del veredicto al completar; lanza `VerificationApiError` si falla o vence el timeout.
    """
    url = f"{settings.api_base_url}/jobs/{job_id}"
    seen: set[str] = set()
    elapsed = 0.0

    async with httpx.AsyncClient(timeout=settings.croma_timeout_seconds) as client:
        while True:
            try:
                resp = await client.get(url)
            except httpx.RequestError as exc:
                raise VerificationApiError(
                    f"error al pollear el job: {exc}", connection_error=True
                ) from exc

            if resp.status_code >= 500:
                raise VerificationApiError(
                    f"la API respondió {resp.status_code} al pollear",
                    status_code=resp.status_code,
                )

            job = (resp.json() or {}).get("data") or {}

            for source in job.get("completedSources", []):
                if source not in seen:
                    seen.add(source)
                    if on_source_done is not None:
                        await on_source_done(source)

            status = job.get("status")
            if status == "completed":
                data = (job.get("result") or {}).get("data")
                if not data:
                    raise VerificationApiError("el job terminó sin veredicto")
                return data
            if status == "failed":
                raise VerificationApiError("el job de verificación falló")

            await asyncio.sleep(interval)
            elapsed += interval
            if elapsed >= timeout:
                raise VerificationApiError("se agotó el tiempo esperando el veredicto")
