"""Worker configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Runtime configuration for the worker process."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5433/ai_job_assistant"
    )
    worker_poll_interval_seconds: int = 60
    log_level: str = "INFO"


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()
