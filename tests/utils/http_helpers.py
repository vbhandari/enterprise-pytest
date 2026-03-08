"""
HTTP request helpers and shortcuts.

Provides convenience functions for common API interaction patterns
used across test suites — registration, login, product creation,
order creation, and status transitions.
"""

from __future__ import annotations

from typing import Any

import httpx

from tests.factories import (
    CouponFactory,
    CustomerFactory,
    ProductFactory,
)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


async def register_customer(
    client: httpx.AsyncClient,
    **overrides: Any,
) -> dict[str, Any]:
    """Register a customer and return the response data."""
    data = CustomerFactory(**overrides)
    resp = await client.post("/auth/register", json=data)
    resp.raise_for_status()
    result = resp.json()
    result["_password"] = data["password"]
    return result


async def login(
    client: httpx.AsyncClient,
    email: str,
    password: str,
) -> str:
    """Log in and return the access token."""
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def auth_header(
    client: httpx.AsyncClient,
    email: str,
    password: str,
) -> dict[str, str]:
    """Log in and return an Authorization header dict."""
    token = await login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Product helpers
# ---------------------------------------------------------------------------


async def create_product(
    admin_client: httpx.AsyncClient,
    **overrides: Any,
) -> dict[str, Any]:
    """Create a product via the API and return the response data."""
    data = ProductFactory(**overrides)
    resp = await admin_client.post("/products", json=data)
    resp.raise_for_status()
    return resp.json()


async def create_products(
    admin_client: httpx.AsyncClient,
    count: int = 3,
    **overrides: Any,
) -> list[dict[str, Any]]:
    """Create multiple products and return their response data."""
    return [await create_product(admin_client, **overrides) for _ in range(count)]


# ---------------------------------------------------------------------------
# Order helpers
# ---------------------------------------------------------------------------


async def create_order(
    customer_client: httpx.AsyncClient,
    product_ids_quantities: list[tuple[int, int]],
) -> dict[str, Any]:
    """
    Create an order and return the response data.

    Args:
        customer_client: Authenticated customer httpx client.
        product_ids_quantities: List of (product_id, quantity) tuples.
    """
    items = [{"product_id": pid, "quantity": qty} for pid, qty in product_ids_quantities]
    resp = await customer_client.post("/orders", json={"items": items})
    resp.raise_for_status()
    return resp.json()


async def transition_order(
    admin_client: httpx.AsyncClient,
    order_id: int,
    new_status: str,
) -> dict[str, Any]:
    """Transition an order to a new status and return the response data."""
    resp = await admin_client.patch(
        f"/orders/{order_id}/status",
        json={"status": new_status},
    )
    resp.raise_for_status()
    return resp.json()


async def create_order_and_pay(
    admin_client: httpx.AsyncClient,
    customer_client: httpx.AsyncClient,
    *,
    product_count: int = 1,
    quantity: int = 2,
    price: float = 25.00,
    stock: int = 100,
) -> dict[str, Any]:
    """
    Full helper: create products, create an order, and pay for it.

    Returns the paid order response.
    """
    products = await create_products(
        admin_client,
        count=product_count,
        price=price,
        stock_quantity=stock,
    )
    items = [(p["id"], quantity) for p in products]
    order = await create_order(customer_client, items)
    paid = await transition_order(admin_client, order["id"], "paid")
    return paid


# ---------------------------------------------------------------------------
# Coupon helpers
# ---------------------------------------------------------------------------


async def create_coupon(
    admin_client: httpx.AsyncClient,
    **overrides: Any,
) -> dict[str, Any]:
    """Create a coupon via the API and return the response data."""
    data = CouponFactory(**overrides)
    resp = await admin_client.post("/coupons", json=data)
    resp.raise_for_status()
    return resp.json()


async def apply_coupon(
    customer_client: httpx.AsyncClient,
    order_id: int,
    coupon_code: str,
) -> dict[str, Any]:
    """Apply a coupon to an order and return the response data."""
    resp = await customer_client.post(
        f"/orders/{order_id}/apply-coupon",
        json={"coupon_code": coupon_code},
    )
    resp.raise_for_status()
    return resp.json()
