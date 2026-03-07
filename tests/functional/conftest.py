"""Functional test suite conftest — shared fixtures for feature tests."""

from __future__ import annotations

import httpx
import pytest

from tests.utils.http_helpers import create_product, create_products


@pytest.fixture()
async def sample_product(admin_client: httpx.AsyncClient) -> dict:
    """Create a single product and return its response data."""
    return await create_product(admin_client, price=29.99, stock_quantity=100)


@pytest.fixture()
async def sample_products(admin_client: httpx.AsyncClient) -> list[dict]:
    """Create three products and return their response data."""
    return await create_products(admin_client, count=3, price=19.99, stock_quantity=50)
