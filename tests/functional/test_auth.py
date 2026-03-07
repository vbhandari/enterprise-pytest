"""Functional tests for authentication endpoints."""

from __future__ import annotations

import httpx
import pytest

from tests.factories import CustomerFactory
from tests.plugins.pytest_enterprise import test_meta
from tests.utils.assertions import assert_error_detail, assert_json_keys, assert_status

pytestmark = pytest.mark.functional


class TestRegistration:
    """POST /auth/register"""

    @test_meta(ticket="AUTH-001", severity="critical", component="auth")
    async def test_register_success(self, client: httpx.AsyncClient) -> None:
        data = CustomerFactory()
        resp = await client.post("/auth/register", json=data)
        assert_status(resp, 201)
        body = resp.json()
        assert_json_keys(body, "id", "name", "email", "role")
        assert body["email"] == data["email"]
        assert body["role"] == "customer"

    @test_meta(ticket="AUTH-002", severity="normal", component="auth")
    async def test_register_duplicate_email(self, client: httpx.AsyncClient) -> None:
        data = CustomerFactory()
        await client.post("/auth/register", json=data)
        resp = await client.post("/auth/register", json=data)
        assert_status(resp, 409)
        assert_error_detail(resp, substring="already registered")

    @test_meta(ticket="AUTH-003", severity="normal", component="auth")
    async def test_register_short_password(self, client: httpx.AsyncClient) -> None:
        data = CustomerFactory(password="short")
        resp = await client.post("/auth/register", json=data)
        assert_status(resp, 422)

    @test_meta(ticket="AUTH-004", severity="normal", component="auth")
    async def test_register_missing_fields(self, client: httpx.AsyncClient) -> None:
        resp = await client.post("/auth/register", json={})
        assert_status(resp, 422)


class TestLogin:
    """POST /auth/login"""

    @test_meta(ticket="AUTH-010", severity="critical", component="auth")
    async def test_login_success(self, client: httpx.AsyncClient) -> None:
        data = CustomerFactory()
        await client.post("/auth/register", json=data)
        resp = await client.post(
            "/auth/login",
            json={"email": data["email"], "password": data["password"]},
        )
        assert_status(resp, 200)
        assert_json_keys(resp.json(), "access_token")

    @test_meta(ticket="AUTH-011", severity="normal", component="auth")
    async def test_login_wrong_password(self, client: httpx.AsyncClient) -> None:
        data = CustomerFactory()
        await client.post("/auth/register", json=data)
        resp = await client.post(
            "/auth/login",
            json={"email": data["email"], "password": "WrongPass999!"},
        )
        assert_status(resp, 401)

    @test_meta(ticket="AUTH-012", severity="normal", component="auth")
    async def test_login_nonexistent_email(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "Whatever123!"},
        )
        assert_status(resp, 401)

    @test_meta(ticket="AUTH-013", severity="normal", component="auth")
    async def test_token_grants_access(self, customer_client: httpx.AsyncClient) -> None:
        resp = await customer_client.get("/orders")
        assert_status(resp, 200)

    @test_meta(ticket="AUTH-014", severity="normal", component="auth")
    async def test_invalid_token_rejected(self, client: httpx.AsyncClient) -> None:
        client.headers["Authorization"] = "Bearer invalid.token.here"
        resp = await client.get("/orders")
        assert_status(resp, 401)
