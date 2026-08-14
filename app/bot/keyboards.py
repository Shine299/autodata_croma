"""D-07 — Teclados inline del bot.

Construye los botones que cuelgan del mensaje de veredicto. El `callback_data` va
namespaced por prefijo (`accion:vid`) para que el router de `handlers.on_callback`
sepa qué hacer sin ambigüedad.

Boilerplate del teclado = delegable (07-AGENTS). El destino de cada botón lo decide
el humano (ver `handlers.on_callback`).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Prefijos de callback (contrato con handlers.on_callback).
CB_DETAIL = "detail"
CB_APPRAISE = "appraise"
CB_SELLER = "seller"
CB_NEW = "new"


def verdict_keyboard(verification_id: str) -> InlineKeyboardMarkup:
    """Los 4 botones bajo un veredicto: detalle, precio, vendedor, nueva consulta."""
    vid = verification_id
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔍 Ver detalle", callback_data=f"{CB_DETAIL}:{vid}"),
                InlineKeyboardButton("💰 Calcular precio", callback_data=f"{CB_APPRAISE}:{vid}"),
            ],
            [
                InlineKeyboardButton("🧑 Verificar vendedor", callback_data=f"{CB_SELLER}:{vid}"),
                InlineKeyboardButton("🔄 Nueva consulta", callback_data=f"{CB_NEW}:"),
            ],
        ]
    )
