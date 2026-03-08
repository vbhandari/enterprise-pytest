"""Smoke tests to verify the fixture infrastructure works end-to-end."""

from __future__ import annotations

import httpx
import pytest

from tests.config import TestSettings
from tests.factories import CustomerFactory, ProductFactory


@pytest.mark.functional
class TestClientFixtures:
    """Verify the httpx client fixtures connect to the FastAPI app."""

    async def test_health_endpoint(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    async def test_admin_client_is_authenticated(self, admin_client: httpx.AsyncClient) -> None:
        # Admin can create a product (requires auth)
        product = ProductFactory()
        resp = await admin_client.post("/products", json=product)
        assert resp.status_code == 201

    async def test_customer_client_is_authenticated(
        self, customer_client: httpx.AsyncClient
    ) -> None:
        # Customer can list their orders (requires auth)
        resp = await customer_client.get("/orders")
        assert resp.status_code == 200

    async def test_unauthenticated_client_is_rejected(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/orders")
        assert resp.status_code == 401


class TestSettingsFixture:
    """Verify test settings fixture."""

    def test_settings_type(self, test_settings: TestSettings) -> None:
        assert isinstance(test_settings, TestSettings)
        assert test_settings.env in ("local", "staging", "ci")

    def test_env_fixture(self, test_env: str) -> None:
        assert test_env in ("local", "staging", "ci")


class TestFactories:
    """Verify factories produce valid data."""

    def test_customer_factory(self) -> None:
        data = CustomerFactory()
        assert isinstance(data, dict)
        assert "email" in data
        assert "password" in data
        assert data["role"] == "customer"

    def test_product_factory(self) -> None:
        data = ProductFactory()
        assert isinstance(data, dict)
        assert "name" in data
        assert data["price"] > 0
        assert data["stock_quantity"] >= 1
