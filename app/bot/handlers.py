"""D-01 — Handlers del esqueleto del bot: /start y /ayuda.

Copy provisional (placeholder). El tono final en español peruano lo cierra P5
(ver 07-AGENTS.md §"Qué NO delegar").
"""

from telegram import Update
from telegram.ext import ContextTypes

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
