"""Application configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "Lead Generation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # OpenAI / OpenRouter
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7

    # Apify
    APIFY_API_TOKEN: str
    APIFY_GOOGLE_MAPS_ACTOR_ID: str = "compass~crawler-google-places"

    # CORS — comma-separated string, e.g. "http://localhost:3000,http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Playwright
    PLAYWRIGHT_HEADLESS: bool = True
    PLAYWRIGHT_TIMEOUT: int = 30000

    # API Keys / Security
    API_KEY_HEADER: str = "X-API-Key"
    SECRET_KEY: str = "change-me-in-production"
    API_KEY: str = ""

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
