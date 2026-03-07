"""Playwright UI tests for the admin login page."""

from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.plugins.pytest_enterprise import test_meta

pytestmark = [pytest.mark.ui]


class TestLoginPage:
    """Admin login page UI tests."""

    @test_meta(ticket="UI-001", severity="critical", component="admin_ui")
    async def test_login_page_loads(self, live_server: str, page: Page) -> None:
        await page.goto(f"{live_server}/admin/login")
        assert await page.title() == "Login | Order Management"
        assert await page.locator("#login-form").is_visible()
        assert await page.locator("#email").is_visible()
        assert await page.locator("#password").is_visible()

    @test_meta(ticket="UI-002", severity="critical", component="admin_ui")
    async def test_login_invalid_credentials(
        self, live_server: str, page: Page
    ) -> None:
        await page.goto(f"{live_server}/admin/login")
        await page.fill("#email", "wrong@example.com")
        await page.fill("#password", "WrongPassword123!")
        await page.click("button[type=submit]")

        # Should stay on login page with error
        error = page.locator("#login-error")
        await error.wait_for(state="visible", timeout=5000)
        assert "invalid" in (await error.text_content() or "").lower()

    @test_meta(ticket="UI-003", severity="normal", component="admin_ui")
    async def test_login_form_requires_fields(
        self, live_server: str, page: Page
    ) -> None:
        await page.goto(f"{live_server}/admin/login")
        # Click submit without filling fields — browser validation should prevent
        await page.click("button[type=submit]")
        # Should still be on login page
        assert "/admin/login" in page.url or "/admin/dashboard" not in page.url
