"""Functional tests for order endpoints."""

from __future__ import annotations

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import (
    assert_order_status,
    assert_order_total_calculation,
    assert_status,
    assert_valid_order_response,
)
from tests.utils.http_helpers import create_order, create_product, transition_order

pytestmark = pytest.mark.functional


class TestOrderCreation:
    """POST /orders"""

    @test_meta(ticket="ORD-001", severity="critical", component="orders")
    async def test_create_order_success(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=25.00, stock_quantity=100)
        resp = await customer_client.post(
            "/orders", json={"items": [{"product_id": product["id"], "quantity": 2}]}
        )
        assert_status(resp, 201)
        data = resp.json()
        assert_valid_order_response(data)
        assert_order_status(data, "created")
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2

    @test_meta(ticket="ORD-002", severity="critical", component="orders")
    async def test_order_calculates_tax(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=100.00, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        assert_order_total_calculation(order, tax_rate=0.08)

    @test_meta(ticket="ORD-003", severity="normal", component="orders")
    async def test_order_insufficient_stock(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=10.00, stock_quantity=2)
        resp = await customer_client.post(
            "/orders", json={"items": [{"product_id": product["id"], "quantity": 999}]}
        )
        assert_status(resp, 409)

    @test_meta(ticket="ORD-004", severity="normal", component="orders")
    async def test_order_invalid_product(
        self, customer_client: httpx.AsyncClient
    ) -> None:
        resp = await customer_client.post(
            "/orders", json={"items": [{"product_id": 99999, "quantity": 1}]}
        )
        assert_status(resp, 404)

    @test_meta(ticket="ORD-005", severity="normal", component="orders")
    async def test_order_empty_items(
        self, customer_client: httpx.AsyncClient
    ) -> None:
        resp = await customer_client.post("/orders", json={"items": []})
        assert_status(resp, 422)

    @test_meta(ticket="ORD-006", severity="normal", component="orders")
    async def test_order_decrements_inventory(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=15.00, stock_quantity=10)
        await create_order(customer_client, [(product["id"], 3)])
        resp = await admin_client.get(f"/products/{product['id']}")
        assert resp.json()["stock_quantity"] == 7


class TestOrderStatusTransitions:
    """PATCH /orders/{id}/status"""

    @test_meta(ticket="ORD-010", severity="critical", component="orders")
    async def test_full_lifecycle(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.00, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        oid = order["id"]

        paid = await transition_order(admin_client, oid, "paid")
        assert_order_status(paid, "paid")

        shipped = await transition_order(admin_client, oid, "shipped")
        assert_order_status(shipped, "shipped")

        delivered = await transition_order(admin_client, oid, "delivered")
        assert_order_status(delivered, "delivered")

    @test_meta(ticket="ORD-011", severity="normal", component="orders")
    async def test_invalid_transition(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.00, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        resp = await admin_client.patch(
            f"/orders/{order['id']}/status", json={"status": "delivered"}
        )
        assert_status(resp, 422)

    @test_meta(ticket="ORD-012", severity="normal", component="orders")
    async def test_cancel_restores_inventory(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=10.00, stock_quantity=20)
        order = await create_order(customer_client, [(product["id"], 5)])

        # Stock should be 15 after order
        resp = await admin_client.get(f"/products/{product['id']}")
        assert resp.json()["stock_quantity"] == 15

        await transition_order(admin_client, order["id"], "cancelled")

        # Stock restored to 20
        resp = await admin_client.get(f"/products/{product['id']}")
        assert resp.json()["stock_quantity"] == 20


class TestOrderListing:
    """GET /orders"""

    @test_meta(ticket="ORD-020", severity="normal", component="orders")
    async def test_customer_sees_own_orders(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=5.00, stock_quantity=100)
        await create_order(customer_client, [(product["id"], 1)])
        resp = await customer_client.get("/orders")
        assert_status(resp, 200)
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @test_meta(ticket="ORD-021", severity="normal", component="orders")
    async def test_admin_sees_all_orders(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=5.00, stock_quantity=100)
        await create_order(customer_client, [(product["id"], 1)])
        resp = await admin_client.get("/orders")
        assert_status(resp, 200)
        assert isinstance(resp.json(), list)
