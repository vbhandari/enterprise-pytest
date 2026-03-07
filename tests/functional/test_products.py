"""Functional tests for product endpoints."""

from __future__ import annotations

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_json_keys, assert_status
from tests.utils.http_helpers import create_product

pytestmark = pytest.mark.functional


class TestProductCRUD:
    """Product create, read, update, delete operations."""

    @test_meta(ticket="PROD-001", severity="critical", component="products")
    async def test_create_product(self, admin_client: httpx.AsyncClient) -> None:
        resp = await admin_client.post(
            "/products",
            json={
                "name": "Widget",
                "description": "A fine widget",
                "price": 9.99,
                "stock_quantity": 50,
                "category": "electronics",
            },
        )
        assert_status(resp, 201)
        body = resp.json()
        assert_json_keys(body, "id", "name", "price", "stock_quantity", "category")
        assert body["name"] == "Widget"
        assert body["price"] == 9.99

    @test_meta(ticket="PROD-002", severity="normal", component="products")
    async def test_list_products(
        self, admin_client: httpx.AsyncClient, sample_products: list[dict]
    ) -> None:
        resp = await admin_client.get("/products")
        assert_status(resp, 200)
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @test_meta(ticket="PROD-003", severity="normal", component="products")
    async def test_get_product_by_id(
        self, client: httpx.AsyncClient, sample_product: dict
    ) -> None:
        resp = await client.get(f"/products/{sample_product['id']}")
        assert_status(resp, 200)
        assert resp.json()["id"] == sample_product["id"]

    @test_meta(ticket="PROD-004", severity="normal", component="products")
    async def test_get_nonexistent_product(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/products/99999")
        assert_status(resp, 404)

    @test_meta(ticket="PROD-005", severity="normal", component="products")
    async def test_update_product(
        self, admin_client: httpx.AsyncClient, sample_product: dict
    ) -> None:
        resp = await admin_client.put(
            f"/products/{sample_product['id']}",
            json={"name": "Updated Widget", "price": 14.99},
        )
        assert_status(resp, 200)
        assert resp.json()["name"] == "Updated Widget"
        assert resp.json()["price"] == 14.99

    @test_meta(ticket="PROD-006", severity="normal", component="products")
    async def test_delete_product(
        self, admin_client: httpx.AsyncClient, sample_product: dict
    ) -> None:
        resp = await admin_client.delete(f"/products/{sample_product['id']}")
        assert_status(resp, 204)
        # Verify soft-deleted (is_active=False but still retrievable by ID)
        resp = await admin_client.get(f"/products/{sample_product['id']}")
        assert_status(resp, 200)
        assert resp.json()["is_active"] is False


class TestProductAuthorization:
    """Verify role-based access for product endpoints."""

    @test_meta(ticket="PROD-010", severity="critical", component="products")
    async def test_customer_cannot_create_product(
        self, customer_client: httpx.AsyncClient
    ) -> None:
        resp = await customer_client.post(
            "/products",
            json={"name": "Hack", "price": 1.0, "stock_quantity": 1, "category": "x"},
        )
        assert_status(resp, 403)

    @test_meta(ticket="PROD-011", severity="normal", component="products")
    async def test_unauthenticated_can_list_products(
        self, client: httpx.AsyncClient
    ) -> None:
        resp = await client.get("/products")
        assert_status(resp, 200)

    @test_meta(ticket="PROD-012", severity="normal", component="products")
    async def test_filter_by_category(
        self, admin_client: httpx.AsyncClient
    ) -> None:
        await create_product(admin_client, category="books", price=12.00)
        await create_product(admin_client, category="electronics", price=50.00)
        resp = await admin_client.get("/products", params={"category": "books"})
        assert_status(resp, 200)
        data = resp.json()
        assert all(p["category"] == "books" for p in data)
