"""Regression tests for order edge cases and previously-fixed bugs."""

from __future__ import annotations

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_status
from tests.utils.http_helpers import create_order, create_product, transition_order

pytestmark = pytest.mark.regression


class TestOrderEdgeCases:
    """Edge cases in order creation and status transitions."""

    @test_meta(ticket="REG-001", severity="critical", component="orders")
    async def test_zero_quantity_rejected(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """BUG: Zero quantity orders were previously accepted."""
        product = await create_product(admin_client, price=10.0, stock_quantity=50)
        resp = await customer_client.post(
            "/orders", json={"items": [{"product_id": product["id"], "quantity": 0}]}
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-002", severity="critical", component="orders")
    async def test_negative_quantity_rejected(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """BUG: Negative quantities caused inventory corruption."""
        product = await create_product(admin_client, price=10.0, stock_quantity=50)
        resp = await customer_client.post(
            "/orders", json={"items": [{"product_id": product["id"], "quantity": -1}]}
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-003", severity="normal", component="orders")
    async def test_cancel_already_cancelled_order(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """BUG: Double cancellation caused double inventory restock."""
        product = await create_product(admin_client, price=10.0, stock_quantity=20)
        order = await create_order(customer_client, [(product["id"], 5)])
        await transition_order(admin_client, order["id"], "cancelled")

        resp = await admin_client.patch(
            f"/orders/{order['id']}/status", json={"status": "cancelled"}
        )
        assert_status(resp, 422)

        # Verify stock is exactly 20 (not 25 from double restock)
        prod_resp = await admin_client.get(f"/products/{product['id']}")
        assert prod_resp.json()["stock_quantity"] == 20

    @test_meta(ticket="REG-004", severity="normal", component="orders")
    async def test_cancel_delivered_order_rejected(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Delivered orders cannot be cancelled."""
        product = await create_product(admin_client, price=10.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        await transition_order(admin_client, order["id"], "paid")
        await transition_order(admin_client, order["id"], "shipped")
        await transition_order(admin_client, order["id"], "delivered")

        resp = await admin_client.patch(
            f"/orders/{order['id']}/status", json={"status": "cancelled"}
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-005", severity="normal", component="orders")
    async def test_multiple_items_in_single_order(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Verify multi-item orders calculate totals correctly."""
        p1 = await create_product(admin_client, price=10.00, stock_quantity=100)
        p2 = await create_product(admin_client, price=25.00, stock_quantity=100)
        p3 = await create_product(admin_client, price=5.50, stock_quantity=100)

        order = await create_order(
            customer_client,
            [(p1["id"], 2), (p2["id"], 1), (p3["id"], 3)],
        )
        # subtotal = 20 + 25 + 16.50 = 61.50
        expected_subtotal = 61.50
        assert abs(order["subtotal"] - expected_subtotal) < 0.02
        assert order["tax_amount"] > 0
        assert order["total"] > order["subtotal"]
