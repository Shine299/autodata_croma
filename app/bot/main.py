"""D-01 — Esqueleto del bot de Telegram con polling.

Arranque local:  python -m app.bot.main
Requiere TELEGRAM_BOT_TOKEN en .env (tarea A-04). Modo polling, sin webhook.
"""

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.bot.handlers import ayuda, on_callback, on_text, start


def build_application() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    # D-02: texto libre (no comandos) → máquina de estados.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    # D-07: botones inline del veredicto.
    app.add_handler(CallbackQueryHandler(on_callback))
    return app


def main() -> None:
    build_application().run_polling()


if __name__ == "__main__":
    main()
