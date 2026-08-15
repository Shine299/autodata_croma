"""Handlers del bot.

- D-01: comandos /start y /ayuda.
- D-02: máquina de estados sobre texto libre (on_text), persistida en `conversations`.

Copy cerrado por P5 (Sprint 2) — tono peruano final, según docs/copy-placeholders-p5.md.
Claves y {placeholders} sin cambios respecto al placeholder original de P3.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.api_client import VerificationApiError, create_verification
from app.bot.formatters import format_verdict
from app.bot.job_client import poll_job, start_async_verification
from app.bot.keyboards import (
    CB_APPRAISE,
    CB_DETAIL,
    CB_NEW,
    CB_SELLER,
    verdict_keyboard,
)
from app.bot.parsers import parse_free_text
from app.bot.states import State
from app.core.database import async_session_maker
from app.repositories.conversation_repo import ConversationRepository

# copy cerrado (P5 — Sprint 2)
_START_TEXT = (
    "¡Hola! Soy *AutoData* 🚗\n"
    "Te ayudo a verificar un auto usado en Perú antes de comprarlo.\n\n"
    "Escríbeme una placa (ej. `ABC-123`) o usa /ayuda para ver qué puedo hacer."
)

# copy cerrado (P5 — Sprint 2)
_AYUDA_TEXT = (
    "*¿Qué puedo hacer?*\n"
    "• Verificar un vehículo por su placa.\n"
    "• Entender texto libre como: `ABC-123 me lo dan a 32 mil`.\n\n"
    "Comandos:\n"
    "/start — empezar\n"
    "/ayuda — esta ayuda"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_START_TEXT, parse_mode="Markdown")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(_AYUDA_TEXT, parse_mode="Markdown")


# --- D-02: máquina de estados sobre texto libre ---------------------------

# copy cerrado (P5 — Sprint 2)
_ASK_PLATE = "Mándame la placa del auto (ej. `ABC-123`) y lo reviso. 🚗"
_ASK_PRICE = "Anotada la placa *{plate}*. ¿A cuánto te lo ofrecen? (ej. `32 mil`)"
_DONE = (
    "Listo: placa *{plate}* a *S/ {price:,.0f}*.\n"
    "_Dame un momento, estoy revisando las fuentes oficiales para darte el veredicto._"
)
# copy cerrado (P5 — Sprint 2). Mensaje amable cuando la API no responde (DoD D-04).
_API_ERROR = (
    "😕 No pude terminar la verificación ahora mismo (una fuente oficial no respondió).\n"
    "Inténtalo de nuevo en un momento, por favor."
)
# copy cerrado (P5 — Sprint 2). Un mensaje por fuente que va llegando (D-05).
_PROGRESS = "🔎 Consultando *{source}*…"


def next_state(current: State, extracted, context: dict) -> tuple[State, dict, str]:
    """Tabla de transiciones (lógica de negocio, decidida a mano — no delegada).

    Devuelve (nuevo_estado, nuevo_contexto, texto_de_respuesta). Función pura:
    no toca la red ni la base, para poder testearla aislada.
    """
    context = dict(context)

    # Una placa nueva en cualquier momento (re)inicia el flujo del vehículo.
    if extracted.plate:
        context["plate"] = extracted.plate
        if extracted.asking_price:
            context["asking_price"] = extracted.asking_price
            return State.DONE, context, _DONE.format(plate=context["plate"], price=context["asking_price"])
        return State.AWAITING_PRICE, context, _ASK_PRICE.format(plate=extracted.plate)

    if current is State.AWAITING_PRICE and extracted.asking_price:
        context["asking_price"] = extracted.asking_price
        return State.DONE, context, _DONE.format(plate=context.get("plate", "?"), price=extracted.asking_price)

    # No entendimos nada útil: pedimos una placa y no cambiamos de estado.
    return current, context, _ASK_PLATE


async def _deliver_verdict(message, ctx: dict) -> None:
    """D-04: llama a POST /verifications y entrega el veredicto formateado.

    Un fallo de la API (502, timeout, red caída) se traduce en `_API_ERROR`, nunca en
    un crash del handler (DoD D-04). El render usa `format_verdict` (D-06) y cuelga los
    4 botones con `verdict_keyboard` (D-07).
    """
    try:
        data = await create_verification(
            plate=ctx.get("plate"),
            asking_price=ctx.get("asking_price"),
        )
    except VerificationApiError:
        await message.reply_text(_API_ERROR, parse_mode="Markdown")
        return

    await _send_verdict(message, data)


async def _send_verdict(message, data: dict) -> None:
    """Render final compartido: veredicto formateado (D-06) + 4 botones (D-07)."""
    vid = data.get("verificationId", "")
    await message.reply_text(
        format_verdict(data),
        parse_mode="Markdown",
        reply_markup=verdict_keyboard(vid),
    )


async def _deliver_verdict_progressive(message, ctx: dict) -> None:
    """D-05: modo asíncrono con mensajes progresivos por fuente.

    Arranca el job (`Prefer: respond-async`) y pollea; por cada fuente que se completa
    manda un mensaje corto, y al final entrega el veredicto. Si el modo async no está
    disponible, cae al veredicto síncrono de D-04 (misma UI, mismo `_API_ERROR`).
    """
    plate = ctx.get("plate")
    price = ctx.get("asking_price")

    try:
        job_id = await start_async_verification(plate, asking_price=price)
    except VerificationApiError:
        # El endpoint async no respondió → fallback al camino síncrono (D-04).
        await _deliver_verdict(message, ctx)
        return

    async def _on_source(source: str) -> None:
        await message.reply_text(_PROGRESS.format(source=source), parse_mode="Markdown")

    try:
        data = await poll_job(job_id, _on_source)
    except VerificationApiError:
        await message.reply_text(_API_ERROR, parse_mode="Markdown")
        return

    await _send_verdict(message, data)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recibe texto libre, avanza la máquina de estados y persiste el resultado."""
    chat_id = str(update.effective_chat.id)
    text = update.message.text or ""

    async with async_session_maker() as session:
        repo = ConversationRepository(session)
        state, ctx = await repo.get(chat_id)
        extracted = parse_free_text(text)
        new_state, new_ctx, reply = next_state(state, extracted, ctx)
        await repo.set(chat_id, new_state, new_ctx)

    await update.message.reply_text(reply, parse_mode="Markdown")

    # D-05: si ya tenemos placa + precio, verificamos en modo progresivo
    # (con fallback síncrono D-04 si el modo async no está disponible).
    if new_state is State.DONE:
        await _deliver_verdict_progressive(update.message, new_ctx)


# --- D-07: botones inline -------------------------------------------------

# copy cerrado (P5 — Sprint 2)
_CB_REPLIES = {
    CB_DETAIL: "Aquí tienes el detalle completo: {vid}",
    CB_APPRAISE: "Dale, ¿a cuánto te lo ofrecen? Escríbeme el precio (ej. `32 mil`).",
    CB_SELLER: "Para revisar al vendedor necesito tu *sí* explícito y su documento.",
    CB_NEW: "¡Listo! Mándame otra placa cuando quieras. 🚗",
}

# Qué estado deja cada botón (destino decidido a mano, no delegado).
_CB_NEXT_STATE = {
    CB_APPRAISE: State.AWAITING_PRICE,
    CB_SELLER: State.AWAITING_SELLER_CONSENT,
    CB_NEW: State.IDLE,
}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Router de los botones inline. Enruta por el prefijo del callback_data."""
    query = update.callback_query
    await query.answer()  # apaga el spinner del botón

    action, _, vid = (query.data or "").partition(":")
    chat_id = str(update.effective_chat.id)

    async with async_session_maker() as session:
        repo = ConversationRepository(session)
        if action == CB_NEW:
            await repo.reset(chat_id)
        elif action in _CB_NEXT_STATE:
            state, ctx = await repo.get(chat_id)
            await repo.set(chat_id, _CB_NEXT_STATE[action], ctx)

    reply = _CB_REPLIES.get(action, "Opción no reconocida.").format(vid=vid or "—")
    await query.edit_message_reply_markup(reply_markup=None)  # evita doble tap
    await query.message.reply_text(reply, parse_mode="Markdown")
