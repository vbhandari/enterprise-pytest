"""
Environment-aware test configuration.

Uses pydantic-settings so values can be overridden via environment variables
prefixed with ``TEST_``.  Defaults target ``local`` (in-process FastAPI app).

Usage in fixtures::

    from tests.config import get_test_settings

    settings = get_test_settings()
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """Central configuration for the test framework."""

    __test__ = False  # Prevent pytest from collecting this as a test class

    model_config = SettingsConfigDict(
        env_prefix="TEST_",
        env_file=".env.test",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    env: Literal["local", "staging", "ci"] = "local"

    # SUT connection
    base_url: str = "http://localhost:8000"

    # Timeouts (seconds)
    default_timeout: float = 10.0
    poll_interval: float = 0.25
    poll_timeout: float = 5.0

    # Test data defaults
    admin_email: str = "admin@test.com"
    admin_password: str = "AdminPass123!"
    customer_email: str = "customer@test.com"
    customer_password: str = "CustPass123!"

    # Feature flags
    capture_responses: bool = False
    run_slow_tests: bool = False

    # Parallel execution
    worker_count: int = 1

    # Reporting
    report_dir: str = "reports"
    attach_screenshots: bool = True


@lru_cache
def get_test_settings() -> TestSettings:
    """Return cached test settings singleton."""
    return TestSettings()
