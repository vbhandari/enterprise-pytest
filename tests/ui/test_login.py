"""Playwright UI tests for the React admin login page."""

from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.plugins.pytest_enterprise import test_meta

pytestmark = [pytest.mark.ui]


class TestLoginPage:
    """Admin login page UI tests — React SPA."""

    @test_meta(ticket="UI-001", severity="critical", component="admin_ui")
    async def test_login_page_loads(self, live_server: str, page: Page) -> None:
        """Login form renders with email, password inputs and submit button."""
        await page.goto(f"{live_server}/admin/login")
        await page.wait_for_selector("[data-testid=email-input]", timeout=5000)

        assert await page.locator("[data-testid=email-input]").is_visible()
        assert await page.locator("[data-testid=password-input]").is_visible()
        assert await page.locator("[data-testid=login-submit]").is_visible()
        assert "Admin Sign In" in (await page.content())

    @test_meta(ticket="UI-002", severity="critical", component="admin_ui")
    async def test_login_invalid_credentials(
        self, live_server: str, page: Page
    ) -> None:
        """Invalid credentials show an error message without navigating away."""
        await page.goto(f"{live_server}/admin/login")
        await page.fill("[data-testid=email-input]", "wrong@example.com")
        await page.fill("[data-testid=password-input]", "WrongPassword123!")
        await page.click("[data-testid=login-submit]")

        error = page.locator("[data-testid=login-error]")
        await error.wait_for(state="visible", timeout=5000)
        error_text = (await error.text_content() or "").lower()
        assert "invalid" in error_text or "wrong" in error_text

    @test_meta(ticket="UI-003", severity="normal", component="admin_ui")
    async def test_login_form_requires_fields(
        self, live_server: str, page: Page
    ) -> None:
        """Submitting with empty fields should not navigate to dashboard."""
        await page.goto(f"{live_server}/admin/login")
        await page.wait_for_selector("[data-testid=login-submit]", timeout=5000)
        await page.click("[data-testid=login-submit]")
        # Browser validation prevents submission — still on login
        assert "dashboard" not in page.url

    @test_meta(ticket="UI-004", severity="normal", component="admin_ui")
    async def test_page_title(self, live_server: str, page: Page) -> None:
        """Page title should reflect the admin app."""
        await page.goto(f"{live_server}/admin/login")
        title = await page.title()
        assert "Admin" in title or "Order" in title
