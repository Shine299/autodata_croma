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

    model_config = {"env_file": ".env"}


settings = Settings()
