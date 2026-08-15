from __future__ import annotations

import asyncio
import json
import time
from datetime import timedelta
from pathlib import Path

import httpx

from app.config import settings
from app.integrations.croma.models import SourceResult

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures"
DEMO_DIR = FIXTURES_DIR / "demo"
MAX_RETRIES = 2


from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.cache_repo import CacheRepository
from app.repositories.quota_repo import QuotaRepository

class CromaClient:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db
        self._client = httpx.AsyncClient(
            base_url=settings.croma_base_url,
            timeout=settings.croma_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.croma_api_key}"},
        )

    async def call(
        self,
        source: str,
        path: str,
        body: dict,
        *,
        cache_key: str = "",
        ttl: timedelta = timedelta(hours=24),
    ) -> SourceResult:
        if settings.croma_mode == "mock":
            return self._mock_call(source, body)

        lookup_key = cache_key or body.get("plate") or body.get("document_number") or "default"
        
        # 1. Intentar leer de caché (read-through)
        if self._db and lookup_key:
            try:
                cache_repo = CacheRepository(self._db)
                cached_data = await cache_repo.get_cached(source, lookup_key)
                if cached_data is not None:
                    # Registrar hit de caché en quota_log
                    quota_repo = QuotaRepository(self._db)
                    await quota_repo.log_quota(
                        source=source,
                        endpoint=path,
                        remaining=None,
                        request_id=None,
                        cache_hit=True,
                        latency_ms=0
                    )
                    
                    found = cached_data.get("found", True) if isinstance(cached_data, dict) else True
                    return SourceResult(
                        source=source,
                        status="ok" if found else "not_found",
                        data=cached_data,
                        latency_ms=0,
                        from_cache=True,
                    )
            except Exception as e:
                # Loguear error de caché pero fallar abierto (continuar a la red)
                print(f"[cache_error] Falló la lectura de caché para {source}: {e}")

        # 2. Caché miss: Realizar llamada de red
        start = time.monotonic()
        last_error: str | None = None
        resp_obj: httpx.Response | None = None

        for attempt in range(1 + MAX_RETRIES):
            try:
                resp = await self._client.post(path, json=body)
                resp_obj = resp
            except httpx.TimeoutException:
                result = SourceResult(
                    source=source,
                    status="error",
                    error="timeout",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
                await self._log_to_db(source, path, resp_obj, result, cache_hit=False)
                return result
            except httpx.HTTPError as exc:
                result = SourceResult(
                    source=source,
                    status="error",
                    error=str(exc),
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
                await self._log_to_db(source, path, resp_obj, result, cache_hit=False)
                return result

            self._log_quota_headers(source, resp)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "2"))
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(retry_after)
                    continue
                result = SourceResult(
                    source=source,
                    status="error",
                    error="rate_limited",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
                await self._log_to_db(source, path, resp, result, cache_hit=False)
                return result

            if resp.status_code >= 400:
                result = SourceResult(
                    source=source,
                    status="error",
                    error=f"http_{resp.status_code}",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
                await self._log_to_db(source, path, resp, result, cache_hit=False)
                return result

            data = resp.json()
            found = data.get("found", True) if isinstance(data, dict) else True
            status = "ok" if found else "not_found"
            
            result = SourceResult(
                source=source,
                status=status,
                data=data,
                latency_ms=int((time.monotonic() - start) * 1000),
            )

            # 3. Guardar en caché tras respuesta exitosa
            if self._db and lookup_key:
                try:
                    cache_repo = CacheRepository(self._db)
                    await cache_repo.set_cached(
                        source=source,
                        lookup_key=lookup_key,
                        payload=data,
                        status=status,
                        ttl_seconds=int(ttl.total_seconds())
                    )
                except Exception as e:
                    print(f"[cache_error] Falló la escritura en caché para {source}: {e}")

            # Registrar llamada en quota_log
            await self._log_to_db(source, path, resp, result, cache_hit=False)
            return result

        result = SourceResult(
            source=source,
            status="error",
            error=last_error or "max_retries",
            latency_ms=int((time.monotonic() - start) * 1000),
        )
        await self._log_to_db(source, path, resp_obj, result, cache_hit=False)
        return result

    async def _log_to_db(
        self, 
        source: str, 
        endpoint: str, 
        resp: httpx.Response | None, 
        result: SourceResult, 
        cache_hit: bool
    ) -> None:
        if not self._db:
            return

        remaining = None
        request_id = None
        if resp is not None:
            remaining_hdr = resp.headers.get("X-RateLimit-Remaining")
            if remaining_hdr is not None and remaining_hdr.isdigit():
                remaining = int(remaining_hdr)
            request_id = resp.headers.get("X-Request-Id")

        try:
            quota_repo = QuotaRepository(self._db)
            await quota_repo.log_quota(
                source=source,
                endpoint=endpoint,
                remaining=remaining,
                request_id=request_id,
                cache_hit=cache_hit,
                latency_ms=result.latency_ms
            )
        except Exception as e:
            print(f"[quota_error] Falló el registro de cuota en base de datos: {e}")

    def _mock_call(self, source: str, body: dict) -> SourceResult:
        # ponytail: linear scan of fixtures dir, glob if fixtures grow past ~50
        lookup = body.get("plate") or body.get("document_number") or body.get("ruc") or "default"
        source_lower = source.lower()
        fixture_path = DEMO_DIR / f"{source_lower}_{lookup}.json"
        if not fixture_path.exists():
            fixture_path = FIXTURES_DIR / f"{source_lower}_{lookup}.json"
        if not fixture_path.exists():
            fixture_path = FIXTURES_DIR / f"{source_lower}_sample.json"
        if not fixture_path.exists():
            return SourceResult(source=source, status="not_found", from_cache=True)
        data = json.loads(fixture_path.read_text())
        return SourceResult(source=source, status="ok", data=data, from_cache=True)

    def _log_quota_headers(self, source: str, resp: httpx.Response) -> None:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        request_id = resp.headers.get("X-Request-Id")
        if remaining is not None or request_id is not None:
            # ponytail: print for now, structured logging when we add observability
            print(f"[quota] {source} remaining={remaining} request_id={request_id}")

    async def close(self) -> None:
        await self._client.aclose()


from fastapi import Depends
from app.core.database import get_db

def get_croma_client(db: AsyncSession = Depends(get_db)) -> CromaClient:
    return CromaClient(db)

