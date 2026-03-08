"""
Root conftest — plugin registration and framework-wide fixtures.

Layered fixture architecture:
  - Session-scoped: async engine, app, base clients
  - Function-scoped: per-test DB transaction (auto-rollback), authenticated clients

This file is loaded automatically by pytest before any tests run.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import httpx
import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sut.app.auth.passwords import hash_password
from sut.app.database import Base, get_db
from sut.app.events.broker import event_broker
from sut.app.main import create_app
from sut.app.models.customer import Customer
from tests.config import TestSettings, get_test_settings
from tests.factories import AdminFactory, CustomerFactory
from tests.plugins.pytest_enterprise import (  # noqa: F401
    ExchangeStore,
    get_test_meta,
    pytest_addoption,
    pytest_configure,
)

# ---------------------------------------------------------------------------
# Exchange store fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def exchange_store() -> ExchangeStore:
    """Provide a clean ExchangeStore for each test."""
    store = ExchangeStore()
    yield store  # type: ignore[misc]
    store.clear()


# ---------------------------------------------------------------------------
# Environment-aware settings fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_env(request: pytest.FixtureRequest) -> str:
    """Return the target test environment from the CLI option."""
    return request.config.getoption("--test-env")


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Return the cached TestSettings instance."""
    return get_test_settings()


# ---------------------------------------------------------------------------
# Async database engine & session (session-scoped, in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
async def async_engine():
    """Create a session-scoped async engine backed by in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_factory(async_engine):
    """Return a sessionmaker bound to the test engine."""
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture()
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test DB session wrapped in a transaction that rolls back after the test.

    This gives each test a clean database state without recreating tables.
    """
    async with session_factory() as session, session.begin():
        yield session
        # Rollback happens automatically when the context manager exits
        await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI app + httpx test client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app(async_engine, session_factory):
    """Create the FastAPI app with the test DB wired in."""
    application = create_app()

    # Override the get_db dependency to use the test session
    async def _test_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db] = _test_get_db
    return application


@pytest.fixture()
async def client(app) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Per-test async HTTP client targeting the FastAPI app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helper fixtures
# ---------------------------------------------------------------------------


async def _register_via_api(
    client: httpx.AsyncClient,
    user_data: dict[str, Any],
) -> None:
    """Register a customer via the public API endpoint."""
    resp = await client.post("/auth/register", json=user_data)
    resp.raise_for_status()


async def _seed_admin_via_db(
    session_factory: async_sessionmaker[AsyncSession],
    user_data: dict[str, Any],
) -> None:
    """Insert an admin user directly into the DB (API always creates customers)."""
    async with session_factory() as session:
        admin = Customer(
            name=user_data["name"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            role="admin",
        )
        session.add(admin)
        await session.commit()


async def _login(
    client: httpx.AsyncClient,
    email: str,
    password: str,
) -> None:
    """Log in and set the Authorization header on the client."""
    login_resp = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    login_resp.raise_for_status()
    token = login_resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture()
async def admin_client(app, session_factory) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Authenticated httpx client with admin role."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        user_data = AdminFactory()
        await _seed_admin_via_db(session_factory, user_data)
        await _login(ac, user_data["email"], user_data["password"])
        yield ac


@pytest.fixture()
async def customer_client(app) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Authenticated httpx client with customer role."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        user_data = CustomerFactory()
        await _register_via_api(ac, user_data)
        await _login(ac, user_data["email"], user_data["password"])
        yield ac


# ---------------------------------------------------------------------------
# Event broker reset
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_event_broker():
    """Clear event broker history and subscribers between tests."""
    event_broker.clear_history()
    yield
    event_broker.clear_history()


# ---------------------------------------------------------------------------
# Exchange capture hook — attach exchange data to report on failure
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _attach_exchange_report(
    request: pytest.FixtureRequest,
    exchange_store: ExchangeStore,
) -> None:
    """After each test, attach captured HTTP exchanges to the test report."""
    yield  # type: ignore[misc]
    if exchange_store.exchanges:
        request.node.user_properties.append(("exchange_report", exchange_store.format_for_report()))
