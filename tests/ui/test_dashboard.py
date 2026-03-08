"""Playwright UI tests for the React admin dashboard."""

from __future__ import annotations

import pytest
from playwright.async_api import Page

from tests.plugins.pytest_enterprise import test_meta

pytestmark = [pytest.mark.ui]


async def _inject_auth_token(page: Page, live_server: str) -> None:
    """
    Inject a fake JWT into localStorage so the React SPA considers
    us authenticated. The actual API calls will fail, but the SPA
    shell (sidebar, routing) will render.

    For a full integration flow, the live server would need a seeded
    admin user — here we focus on testing the React UI layer.
    """
    await page.goto(f"{live_server}/admin/login")
    await page.evaluate('localStorage.setItem("admin_token", "test-token-for-ui")')
    await page.goto(f"{live_server}/admin/dashboard")


class TestDashboard:
    """Admin dashboard UI tests — React SPA."""

    @test_meta(ticket="UI-010", severity="normal", component="admin_ui")
    async def test_unauthenticated_sees_login(self, live_server: str, page: Page) -> None:
        """Without a token, the SPA should show the login form."""
        await page.goto(f"{live_server}/admin/dashboard")
        await page.wait_for_selector("[data-testid=email-input]", timeout=5000)
        assert await page.locator("[data-testid=email-input]").is_visible()

    @test_meta(ticket="UI-011", severity="normal", component="admin_ui")
    async def test_authenticated_sees_dashboard(self, live_server: str, page: Page) -> None:
        """With a token, the SPA should render the dashboard heading."""
        await _inject_auth_token(page, live_server)
        heading = page.locator("[data-testid=dashboard-heading]")
        await heading.wait_for(state="visible", timeout=5000)
        assert "Dashboard" in (await heading.text_content() or "")

    @test_meta(ticket="UI-012", severity="normal", component="admin_ui")
    async def test_sidebar_navigation_links(self, live_server: str, page: Page) -> None:
        """Sidebar should contain navigation links for all sections."""
        await _inject_auth_token(page, live_server)
        sidebar = page.locator("aside")
        await sidebar.wait_for(state="visible", timeout=5000)

        for label in ["Dashboard", "Orders", "Products", "Coupons"]:
            link = sidebar.locator(f"text={label}")
            assert await link.is_visible(), f"Sidebar link '{label}' not visible"

    @test_meta(ticket="UI-013", severity="normal", component="admin_ui")
    async def test_logout_clears_token(self, live_server: str, page: Page) -> None:
        """Clicking sign out should clear the token and show login."""
        await _inject_auth_token(page, live_server)
        await page.click("[data-testid=logout-btn]")
        # After logout, login form should appear
        await page.wait_for_selector("[data-testid=email-input]", timeout=5000)
        assert await page.locator("[data-testid=email-input]").is_visible()
        # Token should be cleared
        token = await page.evaluate('localStorage.getItem("admin_token")')
        assert token is None

    @test_meta(ticket="UI-014", severity="normal", component="admin_ui")
    async def test_navigate_to_orders_page(self, live_server: str, page: Page) -> None:
        """Clicking Orders in sidebar should navigate to the orders page."""
        await _inject_auth_token(page, live_server)
        await page.click("aside >> text=Orders")
        await page.wait_for_selector("[data-testid=status-filters]", timeout=5000)
        assert "/orders" in page.url

    @test_meta(ticket="UI-015", severity="normal", component="admin_ui")
    async def test_navigate_to_products_page(self, live_server: str, page: Page) -> None:
        """Clicking Products in sidebar should navigate to the products page."""
        await _inject_auth_token(page, live_server)
        await page.click("aside >> text=Products")
        await page.wait_for_url("**/products", timeout=5000)
        assert "/products" in page.url
