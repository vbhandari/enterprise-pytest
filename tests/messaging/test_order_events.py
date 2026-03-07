"""Messaging tests for order lifecycle events."""

from __future__ import annotations

import httpx
import pytest

from sut.app.events.broker import EventType, event_broker
from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import (
    assert_event_count,
    assert_event_published,
    assert_no_event_published,
)
from tests.utils.http_helpers import create_order, create_product, transition_order

pytestmark = pytest.mark.messaging


class TestOrderCreatedEvent:
    """Events published when an order is created."""

    @test_meta(ticket="MSG-001", severity="critical", component="events")
    async def test_order_created_event_published(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])

        event = assert_event_published(
            EventType.ORDER_CREATED,
            payload_contains={"order_id": order["id"]},
        )
        assert event.payload["order_id"] == order["id"]

    @test_meta(ticket="MSG-002", severity="normal", component="events")
    async def test_inventory_decremented_event_on_order(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=10.0, stock_quantity=30)
        await create_order(customer_client, [(product["id"], 3)])

        assert_event_published(EventType.INVENTORY_DECREMENTED)

    @test_meta(ticket="MSG-003", severity="normal", component="events")
    async def test_no_event_on_failed_order(
        self, customer_client: httpx.AsyncClient
    ) -> None:
        """Failed order creation should not publish events."""
        event_broker.clear_history()
        await customer_client.post(
            "/orders", json={"items": [{"product_id": 99999, "quantity": 1}]}
        )
        assert_no_event_published(EventType.ORDER_CREATED)


class TestOrderStatusEvents:
    """Events published on order status transitions."""

    @test_meta(ticket="MSG-010", severity="critical", component="events")
    async def test_paid_event_published(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        event_broker.clear_history()

        await transition_order(admin_client, order["id"], "paid")
        assert_event_published(EventType.ORDER_PAID)

    @test_meta(ticket="MSG-011", severity="normal", component="events")
    async def test_shipped_event_published(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        await transition_order(admin_client, order["id"], "paid")
        event_broker.clear_history()

        await transition_order(admin_client, order["id"], "shipped")
        assert_event_published(EventType.ORDER_SHIPPED)

    @test_meta(ticket="MSG-012", severity="normal", component="events")
    async def test_cancelled_event_published(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        event_broker.clear_history()

        await transition_order(admin_client, order["id"], "cancelled")
        assert_event_published(EventType.ORDER_CANCELLED)
        assert_event_published(EventType.INVENTORY_RESTORED)

    @test_meta(ticket="MSG-013", severity="normal", component="events")
    async def test_no_event_on_invalid_transition(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        event_broker.clear_history()

        # created -> delivered is invalid
        await admin_client.patch(
            f"/orders/{order['id']}/status", json={"status": "delivered"}
        )
        assert_no_event_published(EventType.ORDER_DELIVERED)


class TestEventMetadata:
    """Verify event payload structure and ordering."""

    @test_meta(ticket="MSG-020", severity="normal", component="events")
    async def test_event_has_required_fields(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        await create_order(customer_client, [(product["id"], 1)])

        event = assert_event_published(EventType.ORDER_CREATED)
        assert event.event_id  # non-empty UUID
        assert event.timestamp is not None
        assert "order_id" in event.payload

    @test_meta(ticket="MSG-021", severity="normal", component="events")
    async def test_full_lifecycle_event_count(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Full order lifecycle should produce the expected number of events."""
        product = await create_product(admin_client, price=20.0, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        oid = order["id"]

        await transition_order(admin_client, oid, "paid")
        await transition_order(admin_client, oid, "shipped")
        await transition_order(admin_client, oid, "delivered")

        assert_event_count(EventType.ORDER_CREATED, 1)
        assert_event_count(EventType.ORDER_PAID, 1)
        assert_event_count(EventType.ORDER_SHIPPED, 1)
        assert_event_count(EventType.ORDER_DELIVERED, 1)


class TestMultipleSubscribers:
    """Verify multiple subscribers receive events."""

    @test_meta(ticket="MSG-030", severity="normal", component="events")
    async def test_multiple_subscribers_receive_event(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        received: list[dict] = []

        async def subscriber_a(event):
            received.append({"subscriber": "a", "type": str(event.event_type)})

        async def subscriber_b(event):
            received.append({"subscriber": "b", "type": str(event.event_type)})

        event_broker.subscribe(EventType.ORDER_CREATED, subscriber_a)
        event_broker.subscribe(EventType.ORDER_CREATED, subscriber_b)

        try:
            product = await create_product(admin_client, price=10.0, stock_quantity=50)
            await create_order(customer_client, [(product["id"], 1)])

            a_events = [r for r in received if r["subscriber"] == "a"]
            b_events = [r for r in received if r["subscriber"] == "b"]
            assert len(a_events) >= 1
            assert len(b_events) >= 1
        finally:
            event_broker.unsubscribe(EventType.ORDER_CREATED, subscriber_a)
            event_broker.unsubscribe(EventType.ORDER_CREATED, subscriber_b)
