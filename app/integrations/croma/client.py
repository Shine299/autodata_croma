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
MAX_RETRIES = 2


class CromaClient:
    def __init__(self) -> None:
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

        start = time.monotonic()
        last_error: str | None = None

        for attempt in range(1 + MAX_RETRIES):
            try:
                resp = await self._client.post(path, json=body)
            except httpx.TimeoutException:
                return SourceResult(
                    source=source,
                    status="error",
                    error="timeout",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )
            except httpx.HTTPError as exc:
                return SourceResult(
                    source=source,
                    status="error",
                    error=str(exc),
                    latency_ms=int((time.monotonic() - start) * 1000),
                )

            self._log_quota_headers(source, resp)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "2"))
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(retry_after)
                    continue
                return SourceResult(
                    source=source,
                    status="error",
                    error="rate_limited",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )

            if resp.status_code >= 400:
                return SourceResult(
                    source=source,
                    status="error",
                    error=f"http_{resp.status_code}",
                    latency_ms=int((time.monotonic() - start) * 1000),
                )

            data = resp.json()
            found = data.get("found", True) if isinstance(data, dict) else True
            return SourceResult(
                source=source,
                status="ok" if found else "not_found",
                data=data,
                latency_ms=int((time.monotonic() - start) * 1000),
            )

        return SourceResult(
            source=source,
            status="error",
            error=last_error or "max_retries",
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    def _mock_call(self, source: str, body: dict) -> SourceResult:
        # ponytail: linear scan of fixtures dir, glob if fixtures grow past ~50
        lookup = body.get("plate") or body.get("document_number") or "default"
        fixture_path = FIXTURES_DIR / f"{source.lower()}_{lookup}.json"
        if not fixture_path.exists():
            fixture_path = FIXTURES_DIR / f"{source.lower()}_sample.json"
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


def get_croma_client() -> CromaClient:
    return CromaClient()
