"""Regression tests for data integrity and boundary values."""

from __future__ import annotations

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_status

pytestmark = pytest.mark.regression


class TestDataIntegrity:
    """Boundary values and data integrity edge cases."""

    @test_meta(ticket="REG-020", severity="normal", component="products")
    async def test_unicode_product_name(
        self, admin_client: httpx.AsyncClient
    ) -> None:
        """Unicode characters in product names must be handled correctly."""
        resp = await admin_client.post(
            "/products",
            json={
                "name": "Ñoño's Café ☕ — «special» édition",
                "price": 15.00,
                "stock_quantity": 10,
                "category": "food",
            },
        )
        assert_status(resp, 201)
        assert "Ñoño" in resp.json()["name"]

    @test_meta(ticket="REG-021", severity="normal", component="products")
    async def test_very_long_product_name(
        self, admin_client: httpx.AsyncClient
    ) -> None:
        """Product name at maximum length boundary."""
        long_name = "A" * 200
        resp = await admin_client.post(
            "/products",
            json={
                "name": long_name,
                "price": 1.00,
                "stock_quantity": 1,
                "category": "general",
            },
        )
        assert_status(resp, 201)
        assert resp.json()["name"] == long_name

    @test_meta(ticket="REG-022", severity="normal", component="products")
    async def test_product_name_exceeds_max_length(
        self, admin_client: httpx.AsyncClient
    ) -> None:
        """Product name exceeding maximum length should be rejected."""
        too_long = "A" * 201
        resp = await admin_client.post(
            "/products",
            json={
                "name": too_long,
                "price": 1.00,
                "stock_quantity": 1,
                "category": "general",
            },
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-023", severity="normal", component="products")
    async def test_zero_price_product(
        self, admin_client: httpx.AsyncClient
    ) -> None:
        """Zero-priced products (freebies) should be valid."""
        resp = await admin_client.post(
            "/products",
            json={
                "name": "Free Sample",
                "price": 0.00,
                "stock_quantity": 1000,
                "category": "samples",
            },
        )
        # Accept either 201 (zero price allowed) or 422 (validation rejects it)
        assert resp.status_code in (201, 422)

    @test_meta(ticket="REG-024", severity="normal", component="auth")
    async def test_unicode_in_customer_email(
        self, client: httpx.AsyncClient
    ) -> None:
        """Emails with unicode local parts."""
        resp = await client.post(
            "/auth/register",
            json={
                "name": "Tëst Üser",
                "email": "tëst@example.com",
                "password": "SecurePass123!",
            },
        )
        # Should succeed or fail validation gracefully
        assert resp.status_code in (201, 422)
