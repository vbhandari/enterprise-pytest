"""Application configuration via pydantic-settings."""

import pathlib
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root (enterprise-pytest/) regardless of OS or working directory
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "sut" / "data" / "orders.db"
_DEFAULT_DB_URL = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Order Management API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Database
    database_url: str = _DEFAULT_DB_URL
    database_echo: bool = False

    # Auth / JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Tax
    tax_rate: float = 0.08

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
