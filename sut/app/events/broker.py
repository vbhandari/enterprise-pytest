"""In-memory event broker for order lifecycle events."""

import asyncio
import contextlib
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Supported event types in the system."""

    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_COUPON_APPLIED = "order.coupon_applied"
    INVENTORY_DECREMENTED = "inventory.decremented"
    INVENTORY_RESTORED = "inventory.restored"


@dataclass(frozen=True)
class Event:
    """An immutable event published through the broker."""

    event_type: EventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: str = field(default_factory=lambda: "")

    def __post_init__(self) -> None:
        if not self.event_id:
            import uuid

            object.__setattr__(self, "event_id", str(uuid.uuid4()))


# Type alias for subscriber callbacks
Subscriber = Callable[[Event], Coroutine[Any, Any, None]]


class EventBroker:
    """
    Simple in-memory pub/sub event broker.

    Supports:
    - Publishing events to named topics (event types)
    - Multiple subscribers per topic
    - Event history for inspection/testing
    - Async subscriber callbacks
    """

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Subscriber]] = defaultdict(list)
        self._history: list[Event] = []
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, callback: Subscriber) -> None:
        """Register a subscriber for a specific event type."""
        self._subscribers[event_type].append(callback)
        logger.debug("Subscriber registered for %s", event_type)

    def unsubscribe(self, event_type: EventType, callback: Subscriber) -> None:
        """Remove a subscriber for a specific event type."""
        with contextlib.suppress(ValueError):
            self._subscribers[event_type].remove(callback)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers of its type."""
        async with self._lock:
            self._history.append(event)

        logger.info("Event published: %s (id=%s)", event.event_type, event.event_id)

        subscribers = self._subscribers.get(event.event_type, [])
        for subscriber in subscribers:
            try:
                await subscriber(event)
            except Exception:
                logger.exception(
                    "Subscriber error for event %s (id=%s)",
                    event.event_type,
                    event.event_id,
                )

    @property
    def history(self) -> list[Event]:
        """Return a copy of the event history."""
        return list(self._history)

    def get_events_by_type(self, event_type: EventType) -> list[Event]:
        """Return all events of a specific type from history."""
        return [e for e in self._history if e.event_type == event_type]

    def clear_history(self) -> None:
        """Clear the event history. Useful for testing."""
        self._history.clear()

    def clear_all(self) -> None:
        """Clear all subscribers and history. Useful for testing."""
        self._subscribers.clear()
        self._history.clear()


# Singleton broker instance used across the application
event_broker = EventBroker()
