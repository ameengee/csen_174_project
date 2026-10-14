from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------
    # Actual Secrets
    # -----------------------------

    # database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "app"
    db_user: str = "postgres"
    db_pass: str = "postgres"

    # -----------------------------
    # Configs
    # -----------------------------

    # environment setup
    app_env: str = "local"
    json_logs: bool = False
    log_level: str = "INFO"

    # comma-separated list of origins allowed to call the API (the Next.js frontend)
    cors_origins: str = "http://localhost:3000"

    # upload rejection gates
    auto_fail_all: bool = False

    # OpenAI model for profile analysis; the API key comes from OPENAI_API_KEY via the SDK
    openai_model: str = "gpt-5.5"

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Split cors_origins into a list, dropping blanks."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance from environment variables."""
    return Settings()
