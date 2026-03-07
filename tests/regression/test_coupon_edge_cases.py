"""Regression tests for coupon edge cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_status
from tests.utils.http_helpers import create_coupon, create_order, create_product

pytestmark = pytest.mark.regression


class TestCouponEdgeCases:
    """Edge cases in coupon validation and application."""

    @test_meta(ticket="REG-010", severity="critical", component="coupons")
    async def test_expired_coupon_rejected(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Expired coupons must not apply."""
        product = await create_product(admin_client, price=50.0, stock_quantity=50)
        past = (datetime.now(tz=UTC) - timedelta(days=60)).isoformat()
        yesterday = (datetime.now(tz=UTC) - timedelta(days=1)).isoformat()
        coupon = await create_coupon(
            admin_client, valid_from=past, valid_to=yesterday, discount_percent=20.0
        )
        order = await create_order(customer_client, [(product["id"], 1)])
        resp = await customer_client.post(
            f"/orders/{order['id']}/apply-coupon",
            json={"coupon_code": coupon["code"]},
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-011", severity="critical", component="coupons")
    async def test_coupon_not_yet_valid(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Coupons with future valid_from must not apply."""
        product = await create_product(admin_client, price=50.0, stock_quantity=50)
        tomorrow = (datetime.now(tz=UTC) + timedelta(days=1)).isoformat()
        future = (datetime.now(tz=UTC) + timedelta(days=30)).isoformat()
        coupon = await create_coupon(
            admin_client, valid_from=tomorrow, valid_to=future, discount_percent=20.0
        )
        order = await create_order(customer_client, [(product["id"], 1)])
        resp = await customer_client.post(
            f"/orders/{order['id']}/apply-coupon",
            json={"coupon_code": coupon["code"]},
        )
        assert_status(resp, 422)

    @test_meta(ticket="REG-012", severity="normal", component="coupons")
    async def test_coupon_applied_twice_to_same_order(
        self, admin_client: httpx.AsyncClient, customer_client: httpx.AsyncClient
    ) -> None:
        """Applying the same coupon twice should be rejected or idempotent."""
        product = await create_product(admin_client, price=100.0, stock_quantity=50)
        coupon = await create_coupon(admin_client, discount_percent=10.0)
        order = await create_order(customer_client, [(product["id"], 1)])

        # First application
        resp1 = await customer_client.post(
            f"/orders/{order['id']}/apply-coupon",
            json={"coupon_code": coupon["code"]},
        )
        assert_status(resp1, 200)

        # Second application should fail
        resp2 = await customer_client.post(
            f"/orders/{order['id']}/apply-coupon",
            json={"coupon_code": coupon["code"]},
        )
        assert_status(resp2, 409)
