"""Functional tests for coupon endpoints."""

from __future__ import annotations

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_json_keys, assert_status
from tests.utils.http_helpers import (
    apply_coupon,
    create_coupon,
    create_order,
    create_product,
)

pytestmark = pytest.mark.functional


class TestCouponCRUD:
    """Admin coupon management."""

    @test_meta(ticket="CPN-001", severity="critical", component="coupons")
    async def test_create_coupon(self, admin_client: httpx.AsyncClient) -> None:
        coupon = await create_coupon(admin_client, discount_percent=15.0)
        assert_json_keys(coupon, "id", "code", "discount_percent")
        assert coupon["discount_percent"] == 15.0

    @test_meta(ticket="CPN-002", severity="normal", component="coupons")
    async def test_list_coupons(self, admin_client: httpx.AsyncClient) -> None:
        await create_coupon(admin_client)
        resp = await admin_client.get("/coupons")
        assert_status(resp, 200)
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    @test_meta(ticket="CPN-003", severity="normal", component="coupons")
    async def test_customer_cannot_create_coupon(self, customer_client: httpx.AsyncClient) -> None:
        resp = await customer_client.post(
            "/coupons",
            json={
                "code": "HACK",
                "discount_percent": 99,
                "valid_from": "2025-01-01T00:00:00Z",
                "valid_to": "2026-01-01T00:00:00Z",
                "max_uses": 1,
            },
        )
        assert_status(resp, 403)


class TestCouponApplication:
    """POST /orders/{id}/apply-coupon"""

    @test_meta(ticket="CPN-010", severity="critical", component="coupons")
    async def test_apply_coupon_success(
        self,
        admin_client: httpx.AsyncClient,
        customer_client: httpx.AsyncClient,
    ) -> None:
        product = await create_product(admin_client, price=100.00, stock_quantity=50)
        coupon = await create_coupon(admin_client, discount_percent=10.0)
        order = await create_order(customer_client, [(product["id"], 1)])
        updated = await apply_coupon(customer_client, order["id"], coupon["code"])
        assert updated["discount_amount"] > 0
        assert updated["discount_code"] == coupon["code"]
        assert updated["total"] < order["total"]

    @test_meta(ticket="CPN-011", severity="normal", component="coupons")
    async def test_apply_invalid_coupon_code(
        self,
        admin_client: httpx.AsyncClient,
        customer_client: httpx.AsyncClient,
    ) -> None:
        product = await create_product(admin_client, price=50.00, stock_quantity=50)
        order = await create_order(customer_client, [(product["id"], 1)])
        resp = await customer_client.post(
            f"/orders/{order['id']}/apply-coupon",
            json={"coupon_code": "NONEXISTENT"},
        )
        assert_status(resp, 404)
