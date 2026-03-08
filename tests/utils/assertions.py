"""
Domain-specific assertion helpers.

Provides reusable, descriptive assertion functions that produce
clear failure messages and reduce boilerplate in test functions.
"""

from __future__ import annotations

from typing import Any

from sut.app.events.broker import Event, EventType, event_broker
from sut.app.models.order import OrderStatus

# ---------------------------------------------------------------------------
# HTTP response assertions
# ---------------------------------------------------------------------------


def assert_status(response: Any, expected: int, *, msg: str = "") -> None:
    """Assert an HTTP response has the expected status code."""
    actual = response.status_code
    detail = f" — {msg}" if msg else ""
    assert actual == expected, (
        f"Expected status {expected}, got {actual}{detail}.\nResponse body: {response.text[:500]}"
    )


def assert_json_keys(data: dict[str, Any], *keys: str) -> None:
    """Assert that a JSON dict contains all expected keys."""
    missing = set(keys) - set(data.keys())
    assert not missing, f"Missing keys in response: {missing}. Got: {set(data.keys())}"


def assert_error_detail(response: Any, *, substring: str) -> None:
    """Assert the response is an error with a detail message containing substring."""
    body = response.json()
    detail = body.get("detail", "")
    assert substring.lower() in detail.lower(), (
        f"Expected error detail containing '{substring}', got: '{detail}'"
    )


# ---------------------------------------------------------------------------
# Order-specific assertions
# ---------------------------------------------------------------------------


def assert_valid_order_response(data: dict[str, Any]) -> None:
    """Assert that a dict looks like a valid order API response."""
    required = {"id", "customer_id", "status", "subtotal", "tax_amount", "total", "items"}
    missing = required - set(data.keys())
    assert not missing, f"Order response missing keys: {missing}"

    assert data["status"] in [s.value for s in OrderStatus], (
        f"Invalid order status: {data['status']}"
    )
    assert isinstance(data["items"], list), "Order items should be a list"
    assert data["total"] >= 0, f"Order total should be >= 0, got {data['total']}"


def assert_order_status(data: dict[str, Any], expected: str | OrderStatus) -> None:
    """Assert an order response has the expected status."""
    expected_val = expected.value if isinstance(expected, OrderStatus) else expected
    assert data["status"] == expected_val, (
        f"Expected order status '{expected_val}', got '{data['status']}'"
    )


def assert_order_total_calculation(
    data: dict[str, Any],
    *,
    tax_rate: float = 0.08,
    tolerance: float = 0.02,
) -> None:
    """Assert that subtotal + tax - discount ≈ total."""
    subtotal = data.get("subtotal", 0)
    tax = data.get("tax_amount", 0)
    discount = data.get("discount_amount", 0)
    total = data.get("total", 0)

    expected_total = subtotal + tax - discount
    assert abs(total - expected_total) <= tolerance, (
        f"Total mismatch: subtotal={subtotal} + tax={tax} - discount={discount} "
        f"= {expected_total}, but got total={total}"
    )

    expected_tax = round(subtotal * tax_rate, 2)
    assert abs(tax - expected_tax) <= tolerance, (
        f"Tax mismatch: subtotal={subtotal} * rate={tax_rate} = {expected_tax}, but got tax={tax}"
    )


# ---------------------------------------------------------------------------
# Event assertions
# ---------------------------------------------------------------------------


def assert_event_published(
    event_type: EventType | str,
    *,
    payload_contains: dict[str, Any] | None = None,
) -> Event:
    """Assert that an event of the given type was published to the broker."""
    et = EventType(event_type) if isinstance(event_type, str) else event_type
    events = event_broker.get_events_by_type(et)
    assert len(events) > 0, f"Expected event '{et}' to be published, but none found"

    if payload_contains:
        matched = False
        for event in events:
            if all(event.payload.get(k) == v for k, v in payload_contains.items()):
                matched = True
                return event
        assert matched, (
            f"Event '{et}' published but no event matched payload {payload_contains}. "
            f"Found payloads: {[e.payload for e in events]}"
        )

    return events[-1]


def assert_no_event_published(event_type: EventType | str) -> None:
    """Assert that no event of the given type was published."""
    et = EventType(event_type) if isinstance(event_type, str) else event_type
    events = event_broker.get_events_by_type(et)
    assert len(events) == 0, (
        f"Expected no '{et}' events, but found {len(events)}: {[e.payload for e in events]}"
    )


def assert_event_count(event_type: EventType | str, expected: int) -> None:
    """Assert the exact number of events of a given type."""
    et = EventType(event_type) if isinstance(event_type, str) else event_type
    events = event_broker.get_events_by_type(et)
    assert len(events) == expected, f"Expected {expected} '{et}' events, got {len(events)}"
