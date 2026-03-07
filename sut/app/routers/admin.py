"""Admin UI routes — login, logout, dashboard."""

import pathlib
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.auth.jwt import create_access_token, decode_access_token
from sut.app.auth.passwords import verify_password
from sut.app.database import get_db
from sut.app.models.customer import Customer
from sut.app.models.order import Order, OrderStatus
from sut.app.models.product import Product

_APP_DIR = pathlib.Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _APP_DIR / "templates"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_token_from_cookie(request: Request) -> dict[str, str | int] | None:
    """Extract and decode the JWT from the admin_token cookie."""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload.get("role") != "admin":
            return None
        return payload
    except JWTError:
        return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render the admin login page."""
    if _get_token_from_cookie(request):
        return RedirectResponse(url="/admin/dashboard", status_code=302)  # type: ignore[return-value]
    return templates.TemplateResponse(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse:
    """Process admin login form submission."""
    result = await db.execute(
        select(Customer).where(
            Customer.email == email,
            Customer.role == "admin",
            Customer.is_active == True,  # noqa: E712
        )
    )
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(password, admin.hashed_password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Invalid email or password"}
        )

    token = create_access_token(subject=admin.id, role=admin.role)
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=1800,
    )
    return response  # type: ignore[return-value]


@router.get("/logout")
async def logout() -> RedirectResponse:
    """Clear the admin session and redirect to login."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None, alias="status"),
) -> HTMLResponse:
    """Render the admin dashboard with order overview."""
    payload = _get_token_from_cookie(request)
    if not payload:
        return RedirectResponse(url="/admin/login", status_code=302)  # type: ignore[return-value]

    # Gather stats
    total_orders_result = await db.execute(select(func.count(Order.id)))
    total_orders = total_orders_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.CREATED)
    )
    pending_orders = pending_result.scalar() or 0

    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status.in_([OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED])
        )
    )
    total_revenue = float(revenue_result.scalar() or 0)

    total_products_result = await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True)  # noqa: E712
    )
    total_products = total_products_result.scalar() or 0

    stats = {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue,
        "total_products": total_products,
    }

    # Fetch orders with optional status filter
    orders_query = (
        select(Order, Customer.name.label("customer_name"))
        .join(Customer, Order.customer_id == Customer.id)
    )
    if status:
        orders_query = orders_query.where(Order.status == status)
    orders_query = orders_query.order_by(Order.id.desc()).limit(50)

    orders_result = await db.execute(orders_query)
    rows = orders_result.all()

    orders = [
        {
            "id": order.id,
            "customer_name": customer_name,
            "status": order.status,
            "item_count": len(order.items),
            "total": float(order.total),
            "created_at": order.created_at,
        }
        for order, customer_name in rows
    ]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats, "orders": orders, "status_filter": status or ""},
    )
