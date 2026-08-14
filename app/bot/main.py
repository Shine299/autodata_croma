"""D-01 — Esqueleto del bot de Telegram con polling.

Arranque local:  python -m app.bot.main
Requiere TELEGRAM_BOT_TOKEN en .env (tarea A-04). Modo polling, sin webhook.
"""

from telegram.ext import Application, CommandHandler

from app.config import settings
from app.bot.handlers import ayuda, start


def build_application() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    return app


def main() -> None:
    build_application().run_polling()


if __name__ == "__main__":
    main()
