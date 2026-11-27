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
    # full connection string from a hosted provider (Neon, Render); overrides the db_* fields
    database_url: str = ""

    # signs login/verify/reset tokens; must be set to a long random value outside local dev
    jwt_secret: str = "local-dev-only-jwt-secret"

    # Adzuna job search API (all fields and levels); job search skips Adzuna when unset
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""

    # -----------------------------
    # Configs
    # -----------------------------

    # environment setup
    app_env: str = "local"
    json_logs: bool = False
    log_level: str = "INFO"

    # comma-separated list of origins allowed to call the API (the Next.js frontend)
    cors_origins: str = "http://localhost:3000"

    # public URLs used in verify/reset links
    public_api_url: str = "http://localhost:8001"
    frontend_url: str = "http://localhost:3000"

    # no email is actually sent (links are only logged), so hosted sign-ups skip verification
    require_email_verification: bool = True

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

    def model_post_init(self, __context: object) -> None:
        """Refuse to run in prod with the built-in JWT secret."""
        if self.app_env.lower() == "prod" and self.jwt_secret.startswith("local-dev"):
            raise ValueError("JWT_SECRET must be set when APP_ENV=prod")


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance from environment variables."""
    return Settings()
