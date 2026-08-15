"""Handlers del bot.

- D-01: comandos /start y /ayuda.
- D-02: máquina de estados sobre texto libre (on_text), persistida en `conversations`.

Copy cerrado por P5 (Sprint 2) — tono peruano final, según docs/copy-placeholders-p5.md.
Claves y {placeholders} sin cambios respecto al placeholder original de P3.
"""

from telegram import Update
from telegram.ext import ContextTypes

from app.bot.api_client import VerificationApiError, create_verification, create_appraisal
from app.bot.formatters import format_appraisal, format_detail, format_verdict
from app.bot.job_client import poll_job, start_async_verification
from app.core.prompts import FALLBACK_REPLY
from app.integrations.llm import gemini
from app.bot.keyboards import (
    CB_APPRAISE,
    CB_DETAIL,
    CB_NEW,
    CB_SELLER,
    verdict_keyboard,
)
from app.bot.parsers import format_plate_display, parse_free_text
from app.bot.states import State
from app.core.database import async_session_maker
from app.repositories.conversation_repo import ConversationRepository

# copy cerrado (P5 — Sprint 2)
_START_TEXT = (
    "¡Hola! Soy *AutoData* 🚗\n"
    "Te ayudo a verificar un auto usado en Perú antes de comprarlo.\n\n"
    "Escríbeme una placa (ej. `ABC-123`) o usa /ayuda para ver qué puedo hacer."
)

_AYUDA_TEXT = (
    "*AutoData — ¿qué puedo hacer?* 🚗\n"
    "Reviso un auto usado en fuentes oficiales del Estado y te doy un veredicto y un precio justo.\n\n"
    "*Qué reviso (6 fuentes oficiales):*\n"
    "• *SBS* — choques/siniestros reportados (últimos 5 años).\n"
    "• *APESEG* — si el SOAT está vigente.\n"
    "• *SUTRAN* — papeletas a nivel nacional.\n"
    "• *Callao* — papeletas de la provincia del Callao.\n"
    "• *SAT Lima* — deuda (impuesto vehicular + multas).\n"
    "• *SAT Capturas* — orden de captura vigente. 🚨\n"
    "También puedo revisar al *vendedor* (SUNAT + SAT) con su DNI, solo si tú lo autorizas.\n\n"
    "*Ejemplos (cópialos y envíamelos):*\n"
    "• `ABC-123`\n"
    "• `ABC-123 me lo dan a 32 mil`\n"
    "• Luego toca *Verificar vendedor* y manda el DNI + un *sí*.\n\n"
    "*Cómo leer el resultado:*\n"
    "🟢 *LUZ VERDE* — puedes avanzar.\n"
    "🟡 *CON CUIDADO* — hay observaciones, revisa antes.\n"
    "🔴 *ALTO* — mejor no compres.\n"
    "Además te doy un *precio justo* sugerido y un *guion* listo para negociar por WhatsApp.\n\n"
    "Comandos: /start — empezar · /ayuda — esta ayuda\n"
    "_Ojo: no reemplazo una inspección mecánica ni consulto SUNARP/MTC._"
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
# Cuando el bot no puede contactar a su propia API local (uvicorn no está corriendo o
# está en otro puerto). Es un error de configuración, no de una fuente oficial.
_API_DOWN = (
    "🔌 No pude conectar con el servidor de AutoData.\n"
    "Asegúrate de que la API esté corriendo en `http://127.0.0.1:8000`:\n"
    "`.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000`"
)
# copy cerrado (P5 — Sprint 2). Un mensaje por fuente que va llegando (D-05).
_PROGRESS = "🔎 Consultando *{source}*…"


def next_state(current: State, extracted, context: dict, text: str = "") -> tuple[State, dict, str]:
    """Tabla de transiciones (lógica de negocio, decidida a mano — no delegada).

    Devuelve (nuevo_estado, nuevo_contexto, texto_de_respuesta). Función pura:
    no toca la red ni la base, para poder testearla aislada.
    """
    context = dict(context)
    text_lower = text.lower()

    # Una placa nueva en cualquier momento (re)inicia el flujo del vehículo.
    if extracted.plate:
        context["plate"] = extracted.plate
        plate_disp = format_plate_display(extracted.plate)
        if extracted.asking_price:
            context["asking_price"] = extracted.asking_price
            return State.DONE, context, _DONE.format(plate=plate_disp, price=context["asking_price"])
        return State.AWAITING_PRICE, context, _ASK_PRICE.format(plate=plate_disp)

    if current is State.AWAITING_PRICE and extracted.asking_price:
        context["asking_price"] = extracted.asking_price
        if context.get("vid"):
            return State.APPRAISAL_READY, context, "Calculando el precio objetivo…"
        return State.DONE, context, _DONE.format(
            plate=format_plate_display(context.get("plate")), price=extracted.asking_price
        )

    # Flujo de vendedor (D-08)
    if current is State.AWAITING_SELLER_CONSENT:
        has_consent = "si" in text_lower.split() or "sí" in text_lower.split() or "si" == text_lower.strip() or "sí" == text_lower.strip()
        doc = extracted.document_number
        if has_consent and doc:
            context["seller"] = {
                "documentType": "DNI",
                "documentNumber": doc,
                "claimedRole": "PARTICULAR",
                "consent": True
            }
            return State.DONE, context, "Revisando al vendedor y actualizando el veredicto..."
        elif doc and not has_consent:
            return current, context, "Tengo el documento. Para poder consultarlo, respóndeme explícitamente con un *sí*."
        elif has_consent and not doc:
            return current, context, "Permiso registrado. ¿Cuál es el número de documento (DNI) del vendedor?"
        else:
            return current, context, "Para consultar al vendedor necesito el número de documento y que me respondas explícitamente que *sí* autorizas."

    # No entendimos nada útil.
    # Si estábamos esperando el precio, seguimos esperándolo (no re-pedimos la placa).
    if current is State.AWAITING_PRICE and context.get("plate"):
        return State.AWAITING_PRICE, context, _ASK_PRICE.format(
            plate=format_plate_display(context.get("plate"))
        )
    # Para cualquier otro caso (incluidos los estados terminales DONE/APPRAISAL_READY),
    # volvemos a IDLE y pedimos una placa. CLAVE: nunca devolver DONE aquí, o `on_text`
    # re-dispararía una verificación en vano cuando el usuario solo saluda.
    return State.IDLE, context, _ASK_PLATE


# --- IA (solo tono/saludos; el veredicto es 100% determinista) -------------
# Decisión del usuario: la IA NUNCA reescribe el veredicto, los riesgos, la confianza
# ni los números. Solo se usa para la respuesta amable cuando no se entiende el mensaje.
# Falla abierto: si Gemini no está o falla, se usa el texto determinista.


async def _reply_api_error(message, exc: VerificationApiError) -> None:
    """Traduce un `VerificationApiError` al mensaje amable correcto según su causa."""
    if getattr(exc, "connection_error", False):
        # Ni siquiera se pudo contactar a la API local (uvicorn apagado / otro puerto).
        await message.reply_text(_API_DOWN, parse_mode="Markdown")
    elif exc.status_code == 429:
        await message.reply_text(
            "😕 Por el momento hemos alcanzado el límite de consultas al Estado. "
            "Inténtalo de nuevo en un momento.",
            parse_mode="Markdown",
        )
    elif exc.status_code and 400 <= exc.status_code < 500:
        await message.reply_text(f"⚠️ {exc}", parse_mode="Markdown")
    else:
        await message.reply_text(_API_ERROR, parse_mode="Markdown")


async def _natural_fallback(user_message: str) -> str:
    """Respuesta amable cuando no se entiende el mensaje. Cae a `_ASK_PLATE` si la IA falla."""
    if gemini.is_enabled():
        try:
            text = await gemini.naturalize(FALLBACK_REPLY.format(user_message=user_message[:400]))
            if text:
                return text
        except Exception:
            pass
    return _ASK_PLATE


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
            seller=ctx.get("seller"),
        )
    except VerificationApiError as exc:
        await _reply_api_error(message, exc)
        return None

    await _send_verdict(message, data)
    return data


async def _send_verdict(message, data: dict) -> None:
    """Render final compartido: reporte determinista (D-06) + 4 botones (D-07)."""
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
        job_id = await start_async_verification(plate, asking_price=price, seller=ctx.get("seller"))
    except VerificationApiError:
        # El endpoint async no respondió → fallback al camino síncrono (D-04).
        return await _deliver_verdict(message, ctx)

    async def _on_source(source: str) -> None:
        await message.reply_text(_PROGRESS.format(source=source), parse_mode="Markdown")

    try:
        data = await poll_job(job_id, _on_source)
    except VerificationApiError as exc:
        await _reply_api_error(message, exc)
        return None

    await _send_verdict(message, data)
    return data


async def _deliver_appraisal(message, ctx: dict) -> None:
    """D-09: Llama a POST /verifications/{id}/appraisals y formatea el script."""
    vid = ctx.get("vid")
    price = ctx.get("asking_price")
    plate = ctx.get("plate")
    try:
        data = await create_appraisal(verification_id=vid, asking_price=price, plate=plate)
    except VerificationApiError as exc:
        await _reply_api_error(message, exc)
        return

    await message.reply_text(format_appraisal(data), parse_mode="Markdown")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recibe texto libre, avanza la máquina de estados y persiste el resultado."""
    chat_id = str(update.effective_chat.id)
    text = update.message.text or ""

    async with async_session_maker() as session:
        repo = ConversationRepository(session)
        state, ctx = await repo.get(chat_id)
        extracted = parse_free_text(text)
        new_state, new_ctx, reply = next_state(state, extracted, ctx, text)
        await repo.set(chat_id, new_state, new_ctx)

    # Si no entendimos nada, responde con naturalidad (IA) en vez del texto genérico.
    if reply == _ASK_PLATE:
        reply = await _natural_fallback(text)

    await update.message.reply_text(reply, parse_mode="Markdown")

    # D-05: verificamos SOLO si de verdad tenemos placa (y no re-verificamos con un
    # contexto vacío). Guard defensivo: sin placa no se consulta a ninguna fuente.
    if new_state is State.DONE and new_ctx.get("plate"):
        data = await _deliver_verdict_progressive(update.message, new_ctx)
        if data:
            # Guardamos la verificación para el botón "Ver detalle" y para tasar con el id real.
            new_ctx["last_verification"] = data
            new_ctx["vid"] = data.get("verificationId") or new_ctx.get("vid")
            async with async_session_maker() as session:
                await ConversationRepository(session).set(chat_id, new_state, new_ctx)
    elif new_state is State.APPRAISAL_READY and new_ctx.get("vid"):
        await _deliver_appraisal(update.message, new_ctx)


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

    # "Ver detalle": renderiza el desglose completo desde la verificación guardada.
    if action == CB_DETAIL:
        async with async_session_maker() as session:
            _, ctx = await ConversationRepository(session).get(chat_id)
        await query.edit_message_reply_markup(reply_markup=None)
        data = ctx.get("last_verification")
        if data:
            await query.message.reply_text(format_detail(data), parse_mode="Markdown")
        else:
            await query.message.reply_text(
                "No tengo el detalle a la mano. Mándame la placa de nuevo y te lo muestro. 🚗",
                parse_mode="Markdown",
            )
        return

    async with async_session_maker() as session:
        repo = ConversationRepository(session)
        if action == CB_NEW:
            await repo.reset(chat_id)
        elif action in _CB_NEXT_STATE:
            state, ctx = await repo.get(chat_id)
            if action in (CB_APPRAISE, CB_SELLER) and vid:
                ctx["vid"] = vid
            await repo.set(chat_id, _CB_NEXT_STATE[action], ctx)

    reply = _CB_REPLIES.get(action, "Opción no reconocida.").format(vid=vid or "—")
    await query.edit_message_reply_markup(reply_markup=None)  # evita doble tap
    await query.message.reply_text(reply, parse_mode="Markdown")
