"""UI test suite conftest — Playwright fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import pytest
import uvicorn

from sut.app.main import create_app


@pytest.fixture(scope="session")
def _ui_app():
    """Create the FastAPI app for UI testing."""
    return create_app()


@pytest.fixture(scope="session")
async def live_server(_ui_app) -> AsyncGenerator[str, None]:
    """
    Start a live uvicorn server for Playwright to connect to.

    Yields the base URL (e.g. http://127.0.0.1:8001).
    """
    config = uvicorn.Config(
        _ui_app,
        host="127.0.0.1",
        port=8001,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    loop = asyncio.get_event_loop()
    task = loop.create_task(server.serve())

    # Wait for server to start
    for _ in range(50):
        if server.started:
            break
        await asyncio.sleep(0.1)

    yield "http://127.0.0.1:8001"

    server.should_exit = True
    await task
