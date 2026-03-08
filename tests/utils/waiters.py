"""
Async polling helpers for eventual-consistency checks.

Useful when testing asynchronous operations where the result
may not be immediately available (e.g., event propagation).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def poll_until(
    func: Callable[[], Awaitable[T]],
    *,
    predicate: Callable[[T], bool] | None = None,
    timeout: float = 5.0,
    interval: float = 0.25,
    description: str = "condition",
) -> T:
    """
    Repeatedly call an async function until a predicate is satisfied.

    Args:
        func: Async callable to poll.
        predicate: Function that returns True when the result is acceptable.
                   If None, any truthy result is accepted.
        timeout: Maximum seconds to wait.
        interval: Seconds between polls.
        description: Human-readable description for error messages.

    Returns:
        The first result that satisfies the predicate.

    Raises:
        TimeoutError: If the predicate is not satisfied within the timeout.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    last_result: T | None = None

    while asyncio.get_event_loop().time() < deadline:
        result = await func()
        last_result = result

        if predicate is not None:
            if predicate(result):
                return result
        elif result:
            return result

        await asyncio.sleep(interval)

    raise TimeoutError(
        f"Timed out after {timeout}s waiting for {description}. Last result: {last_result}"
    )


async def poll_until_event(
    event_type: str,
    *,
    timeout: float = 5.0,
    interval: float = 0.1,
) -> list:
    """
    Poll the event broker until at least one event of the given type appears.

    Returns:
        List of matching events.
    """
    from sut.app.events.broker import EventType, event_broker

    et = EventType(event_type)

    async def _check() -> list:
        return event_broker.get_events_by_type(et)

    return await poll_until(
        _check,
        predicate=lambda events: len(events) > 0,
        timeout=timeout,
        interval=interval,
        description=f"event '{event_type}'",
    )


async def wait_for_status(
    client,
    order_id: int,
    expected_status: str,
    *,
    timeout: float = 5.0,
    interval: float = 0.25,
) -> dict:
    """
    Poll an order endpoint until it reaches the expected status.

    Returns:
        The order response dict once the status matches.
    """

    async def _check() -> dict:
        resp = await client.get(f"/orders/{order_id}")
        return resp.json()

    return await poll_until(
        _check,
        predicate=lambda data: data.get("status") == expected_status,
        timeout=timeout,
        interval=interval,
        description=f"order {order_id} status='{expected_status}'",
    )
