from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    croma_api_key: str = ""
    croma_base_url: str = "https://api.croma.run"
    croma_mode: str = "mock"
    croma_timeout_seconds: int = 40

    telegram_bot_token: str = ""
    telegram_mode: str = "polling"

    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    app_env: str = "dev"
    public_base_url: str = "http://localhost:8080"
    internal_api_key: str = ""

    # D-04: base de la propia API que el bot consume por HTTP.
    # Debe coincidir con el puerto de uvicorn (por defecto 8000). Se usa 127.0.0.1
    # (no "localhost") porque en Windows "localhost" resuelve a ::1 primero y añade
    # ~2s de retardo por request al caer a IPv4.
    api_base_url: str = "http://127.0.0.1:8000/api/v1"

    model_config = {"env_file": ".env"}


settings = Settings()
