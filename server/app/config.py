from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SENTINELBR_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SentinelBR"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://sentinelbr:sentinelbr@localhost:5432/sentinelbr"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    loki_url: str = Field(default="http://localhost:3100")

    jwt_secret: str = Field(default="change-me-in-prod")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
