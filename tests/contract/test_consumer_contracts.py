"""
Consumer-driven contract tests using Pact.

These tests define the expectations that a hypothetical frontend consumer
has against the Order Management API (provider). The Pact mock server
stands in for the real provider during consumer testing, and the generated
Pact file can later be used for provider verification.

This demonstrates the consumer side of the Pact workflow.
"""

from __future__ import annotations

import json

import httpx
import pytest
from pact import Pact

pytestmark = [pytest.mark.contract]

CONSUMER = "AdminDashboard"
PROVIDER = "OrderManagementAPI"


def _new_pact() -> Pact:
    """Create a fresh Pact instance for each test (v3 requires one per serve)."""
    return Pact(CONSUMER, PROVIDER)


class TestProductContracts:
    """Consumer expectations for the Products API."""

    def test_list_products_contract(self) -> None:
        """Consumer expects GET /products to return a JSON array of products."""
        pact = _new_pact()
        (
            pact.upon_receiving("a request to list products")
            .with_request("GET", "/products")
            .will_respond_with(200)
            .with_body(
                json.dumps([
                    {
                        "id": 1,
                        "name": "Test Widget",
                        "description": "A test product",
                        "price": 29.99,
                        "stock_quantity": 100,
                        "category": "electronics",
                        "is_active": True,
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": "2025-01-01T00:00:00",
                    }
                ]),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.get(f"{srv.url}/products")

            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            product = data[0]
            assert "id" in product
            assert "name" in product
            assert "price" in product
            assert isinstance(product["price"], (int, float))

    def test_get_single_product_contract(self) -> None:
        """Consumer expects GET /products/1 to return a single product."""
        pact = _new_pact()
        (
            pact.upon_receiving("a request to get product 1")
            .with_request("GET", "/products/1")
            .will_respond_with(200)
            .with_body(
                json.dumps({
                    "id": 1,
                    "name": "Premium Gadget",
                    "description": "High-end gadget",
                    "price": 149.99,
                    "stock_quantity": 25,
                    "category": "electronics",
                    "is_active": True,
                    "created_at": "2025-01-01T00:00:00",
                    "updated_at": "2025-01-01T00:00:00",
                }),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.get(f"{srv.url}/products/1")

            assert resp.status_code == 200
            product = resp.json()
            assert product["id"] == 1
            assert product["name"] == "Premium Gadget"
            assert product["price"] == 149.99

    def test_product_not_found_contract(self) -> None:
        """Consumer expects GET /products/99999 to return 404."""
        pact = _new_pact()
        (
            pact.upon_receiving("a request for a non-existent product")
            .with_request("GET", "/products/99999")
            .will_respond_with(404)
            .with_body(
                json.dumps({"detail": "Product not found"}),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.get(f"{srv.url}/products/99999")

            assert resp.status_code == 404
            assert "detail" in resp.json()


class TestAuthContracts:
    """Consumer expectations for the Auth API."""

    def test_login_success_contract(self) -> None:
        """Consumer expects POST /auth/login to return a JWT token."""
        pact = _new_pact()
        (
            pact.upon_receiving("a successful login request")
            .with_request("POST", "/auth/login")
            .with_body(
                json.dumps({
                    "email": "user@test.com",
                    "password": "TestPass123!",
                }),
                content_type="application/json",
            )
            .will_respond_with(200)
            .with_body(
                json.dumps({
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock",
                }),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.post(
                f"{srv.url}/auth/login",
                json={"email": "user@test.com", "password": "TestPass123!"},
            )

            assert resp.status_code == 200
            body = resp.json()
            assert "access_token" in body
            assert isinstance(body["access_token"], str)
            assert len(body["access_token"]) > 0

    def test_login_failure_contract(self) -> None:
        """Consumer expects POST /auth/login with bad creds to return 401."""
        pact = _new_pact()
        (
            pact.upon_receiving("a login request with invalid credentials")
            .with_request("POST", "/auth/login")
            .with_body(
                json.dumps({
                    "email": "wrong@test.com",
                    "password": "BadPass!",
                }),
                content_type="application/json",
            )
            .will_respond_with(401)
            .with_body(
                json.dumps({"detail": "Invalid email or password"}),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.post(
                f"{srv.url}/auth/login",
                json={"email": "wrong@test.com", "password": "BadPass!"},
            )

            assert resp.status_code == 401
            assert "detail" in resp.json()


class TestOrderContracts:
    """Consumer expectations for the Orders API."""

    def test_list_orders_contract(self) -> None:
        """Consumer expects GET /orders to return a list of order summaries."""
        pact = _new_pact()
        (
            pact.upon_receiving("a request to list orders")
            .with_request("GET", "/orders")
            .with_header("Authorization", "Bearer valid-token")
            .will_respond_with(200)
            .with_body(
                json.dumps([
                    {
                        "id": 1,
                        "customer_id": 1,
                        "status": "created",
                        "total": 54.00,
                        "created_at": "2025-01-01T00:00:00",
                    }
                ]),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.get(
                f"{srv.url}/orders",
                headers={"Authorization": "Bearer valid-token"},
            )

            assert resp.status_code == 200
            orders = resp.json()
            assert isinstance(orders, list)
            assert len(orders) >= 1
            order = orders[0]
            assert "id" in order
            assert "status" in order
            assert "total" in order
            assert isinstance(order["total"], (int, float))

    def test_health_check_contract(self) -> None:
        """Consumer expects GET /health to return status healthy."""
        pact = _new_pact()
        (
            pact.upon_receiving("a health check request")
            .with_request("GET", "/health")
            .will_respond_with(200)
            .with_body(
                json.dumps({"status": "healthy", "version": "0.1.0"}),
                content_type="application/json",
            )
        )

        with pact.serve() as srv:
            resp = httpx.get(f"{srv.url}/health")

            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "healthy"
            assert "version" in body
