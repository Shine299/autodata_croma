"""Handlers del bot.

- D-01: comandos /start y /ayuda.
- D-02: máquina de estados sobre texto libre (on_text), persistida en `conversations`.

Copy provisional (placeholder). El tono final en español peruano lo cierra P5
(ver 07-AGENTS.md §"Qué NO delegar").
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.keyboards import CB_APPRAISE, CB_DETAIL, CB_NEW, CB_SELLER
from app.bot.parsers import parse_free_text
from app.bot.states import State
from app.core.database import async_session_maker
from app.repositories.conversation_repo import ConversationRepository

# copy final: P5
_START_TEXT = (
    "¡Hola! Soy *AutoData* 🚗\n"
    "Te ayudo a verificar un auto usado en Perú antes de comprarlo.\n\n"
    "Escríbeme una placa (ej. `ABC-123`) o usa /ayuda para ver qué puedo hacer."
)

# copy final: P5
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

# copy final: P5
_ASK_PLATE = "Mándame la placa del auto (ej. `ABC-123`) y lo reviso. 🚗"
_ASK_PRICE = "Anotada la placa *{plate}*. ¿A cuánto te lo ofrecen? (ej. `32 mil`)"
_DONE = (
    "Listo: placa *{plate}* a *S/ {price:,.0f}*.\n"
    "_(La verificación completa llega cuando la API esté lista — D-04.)_"
)


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


# --- D-07: botones inline -------------------------------------------------

# copy final: P5
_CB_REPLIES = {
    CB_DETAIL: "Abre el detalle completo aquí: {vid}",
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
