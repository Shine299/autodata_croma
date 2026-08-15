"""D-05 — Tests de los mensajes progresivos del bot.

DoD: se ven 4-5 mensajes secuenciales (uno por fuente) y no un único bloque final.
Se mockea el cliente de jobs (`start_async_verification` / `poll_job`) para no depender
de la red ni del timing real.
"""

import json
from pathlib import Path

import pytest
from telegram import InlineKeyboardMarkup

from app.bot import handlers
from app.bot.api_client import VerificationApiError

FIXTURES = Path(__file__).parent / "fixtures"
SOURCES = ["SBS", "APESEG", "SUTRAN", "Callao", "SAT Lima"]


class _FakeMessage:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def reply_text(self, text, parse_mode=None, reply_markup=None):
        self.calls.append({"text": text, "reply_markup": reply_markup})


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_progressive_sends_one_message_per_source_then_verdict(monkeypatch):
    data = _load("verification_go.json")

    async def _start(*args, **kwargs):
        return "job_abc"

    async def _poll(job_id, on_source_done=None, **kwargs):
        for src in SOURCES:  # simula fuentes llegando de a una
            await on_source_done(src)
        return data

    monkeypatch.setattr(handlers, "start_async_verification", _start)
    monkeypatch.setattr(handlers, "poll_job", _poll)

    msg = _FakeMessage()
    await handlers._deliver_verdict_progressive(msg, {"plate": "ABC123", "asking_price": 32000})

    # 5 mensajes de progreso (uno por fuente) + 1 de veredicto = 6, secuenciales.
    assert len(msg.calls) == len(SOURCES) + 1
    # Los primeros son progreso, en orden.
    for i, src in enumerate(SOURCES):
        assert src in msg.calls[i]["text"]
        assert msg.calls[i]["reply_markup"] is None
    # El último es el veredicto con los botones.
    assert isinstance(msg.calls[-1]["reply_markup"], InlineKeyboardMarkup)
    assert "🟢" in msg.calls[-1]["text"]


@pytest.mark.asyncio
async def test_falls_back_to_sync_when_async_unavailable(monkeypatch):
    data = _load("verification_go.json")

    async def _start_fails(*args, **kwargs):
        raise VerificationApiError("no async", status_code=404)

    async def _sync_ok(*args, **kwargs):
        return data

    monkeypatch.setattr(handlers, "start_async_verification", _start_fails)
    monkeypatch.setattr(handlers, "create_verification", _sync_ok)

    msg = _FakeMessage()
    await handlers._deliver_verdict_progressive(msg, {"plate": "ABC123", "asking_price": 32000})

    # Sin progreso, pero sí veredicto (camino síncrono D-04).
    assert len(msg.calls) == 1
    assert isinstance(msg.calls[0]["reply_markup"], InlineKeyboardMarkup)


@pytest.mark.asyncio
async def test_poll_failure_shows_friendly_message(monkeypatch):
    async def _start(*args, **kwargs):
        return "job_abc"

    async def _poll_fails(job_id, on_source_done=None, **kwargs):
        raise VerificationApiError("job failed")

    monkeypatch.setattr(handlers, "start_async_verification", _start)
    monkeypatch.setattr(handlers, "poll_job", _poll_fails)

    msg = _FakeMessage()
    await handlers._deliver_verdict_progressive(msg, {"plate": "ABC123", "asking_price": 32000})

    assert len(msg.calls) == 1
    assert msg.calls[0]["text"] == handlers._API_ERROR
