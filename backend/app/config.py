"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "tweet-brain"
    service_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost,http://localhost:80,http://127.0.0.1,http://127.0.0.1:80"

    database_root: Path = Field(default=Path("../database"))

    x_bearer_token: str = ""

    xai_api_key: str = ""
    xai_model: str = "grok-4.3"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.environment != "development":
            return None
        return r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?$"

    @property
    def groups_path(self) -> Path:
        return self.database_root / "groups.yaml"

    @property
    def posts_dir(self) -> Path:
        return self.database_root / "posts"

    @property
    def runs_dir(self) -> Path:
        return self.database_root / "runs"

    @property
    def settings_path(self) -> Path:
        return self.database_root / "settings.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
