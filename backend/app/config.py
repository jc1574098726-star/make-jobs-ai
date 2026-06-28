from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = BASE_DIR / "data" / "make_jobs.db"
DEFAULT_EXPORT_DIR = BASE_DIR / "data" / "exports"


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_origin: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_ORIGIN")

    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_model: str = Field(default="claude-opus-4-7", alias="CLAUDE_MODEL")
    claude_effort: str = Field(default="high", alias="CLAUDE_EFFORT")
    recommendation_limit: int = Field(default=10, alias="RECOMMENDATION_LIMIT")

    scrape_mode: str = Field(default="real", alias="SCRAPE_MODE")
    browser_headed: bool = Field(default=True, alias="BROWSER_HEADED")

    database_url: str = Field(
        default="sqlite:///{}".format(DEFAULT_DB_PATH.as_posix()),
        alias="DATABASE_URL",
    )
    export_dir: str = Field(default=str(DEFAULT_EXPORT_DIR), alias="EXPORT_DIR")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
