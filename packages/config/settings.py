from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "ai-platform"
    app_version: str = "0.1.0"
    debug: bool = False

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Logfire
    logfire_token: SecretStr | None = None
    logfire_project_name: str = "ai-platform"

    # NestJS downstream service
    nestjs_base_url: str = "https://api.portal.dev.divami.com"
    nestjs_timeout: float = 30.0
    nestjs_max_retries: int = 3

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/platform.db"

    # AI models
    google_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None
    default_model: str = "gemini-2.5-flash"
    groq_model: str = "qwen/qwen3-32b"


    # Azure OpenAI
    azure_openai_model_endpoint: str | None = None
    azure_openai_model_key: SecretStr | None = None
    azure_openai_model_api_version: str = "2024-04-01-preview"


@lru_cache
def get_settings() -> Settings:
    return Settings()
