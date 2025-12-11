"""
Configuration management
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "BaaS Core Banking"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Formance
    formance_base_url: str = "https://api.formance.cloud"
    formance_client_id: str = ""
    formance_client_secret: str = ""
    formance_organization_id: str | None = None
    formance_stack_id: str | None = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database (if needed for local storage)
    database_url: str | None = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis (for caching/sessions)
    redis_url: str | None = None
    redis_max_connections: int = 50

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Monitoring
    sentry_dsn: str | None = None
    enable_metrics: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
