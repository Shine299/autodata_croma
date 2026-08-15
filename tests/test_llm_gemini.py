"""Capa de IA de fraseo (Gemini): siempre debe fallar abierto (devolver None)."""

import httpx
import pytest
from unittest.mock import patch

from app.config import settings
from app.integrations.llm import gemini


@pytest.mark.asyncio
async def test_naturalize_returns_none_without_key():
    # El conftest deja gemini_api_key="" → la IA está apagada y no toca la red.
    assert gemini.is_enabled() is False
    assert await gemini.naturalize("hola") is None


@pytest.mark.asyncio
async def test_naturalize_returns_none_on_network_error():
    settings.gemini_api_key = "test-key"

    class _BoomClient(httpx.AsyncClient):
        def __init__(self, *a, **k):
            k.pop("timeout", None)
            super().__init__()

        async def post(self, *a, **k):
            raise httpx.ConnectError("boom")

    with patch.object(gemini.httpx, "AsyncClient", _BoomClient):
        assert await gemini.naturalize("hola") is None


@pytest.mark.asyncio
async def test_naturalize_parses_gemini_response():
    settings.gemini_api_key = "test-key"

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "Mándame la placa, porfa."}]}}]},
        )

    transport = httpx.MockTransport(_handler)

    class _FakeClient(httpx.AsyncClient):
        def __init__(self, *a, **k):
            k.pop("timeout", None)
            super().__init__(transport=transport)

    with patch.object(gemini.httpx, "AsyncClient", _FakeClient):
        text = await gemini.naturalize("hola")

    assert text == "Mándame la placa, porfa."
