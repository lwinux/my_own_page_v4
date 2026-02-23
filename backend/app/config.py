import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.environ.get("DATABASE_URL")
    DATABASE_SYNC_URL: str = os.environ.get("DATABASE_SYNC_URL")

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Application ───────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost,http://localhost:80"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    FEATURE_RATE_LIMITING: bool = True
    RATE_LIMIT_AUTH: str = "10/minute"

    # ── Feature Flags ─────────────────────────────────────────────────────────
    FEATURE_PDF_EXPORT: bool = False
    FEATURE_THEMES: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
