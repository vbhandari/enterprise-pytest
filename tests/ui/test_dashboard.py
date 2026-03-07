"""Playwright UI tests for the admin dashboard."""

from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.plugins.pytest_enterprise import test_meta

pytestmark = [pytest.mark.ui]


async def _seed_and_login_admin(live_server: str, page: Page) -> None:
    """
    Seed an admin user via the API and log in through the UI.

    Uses the registration endpoint + direct DB manipulation isn't available
    in UI tests, so we register as customer then rely on a pre-seeded admin.
    For UI tests, we POST to login directly.
    """
    # Navigate to login and submit credentials
    await page.goto(f"{live_server}/admin/login")
    await page.fill("#email", "admin@test.com")
    await page.fill("#password", "AdminPass123!")
    await page.click("button[type=submit]")
    # Wait for redirect
    await page.wait_for_url("**/admin/dashboard", timeout=5000)


class TestDashboard:
    """Admin dashboard UI tests."""

    @test_meta(ticket="UI-010", severity="normal", component="admin_ui")
    async def test_dashboard_redirects_unauthenticated(
        self, live_server: str, page: Page
    ) -> None:
        await page.goto(f"{live_server}/admin/dashboard")
        # Should redirect to login
        await page.wait_for_url("**/admin/login", timeout=5000)
        assert "/admin/login" in page.url

    @test_meta(ticket="UI-011", severity="normal", component="admin_ui")
    async def test_logout_redirects_to_login(
        self, live_server: str, page: Page
    ) -> None:
        await page.goto(f"{live_server}/admin/logout")
        await page.wait_for_url("**/admin/login", timeout=5000)
        assert "/admin/login" in page.url
