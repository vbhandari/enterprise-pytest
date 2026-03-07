"""API route modules."""

from sut.app.routers.admin import router as admin_router
from sut.app.routers.auth import router as auth_router
from sut.app.routers.coupons import router as coupons_router
from sut.app.routers.orders import router as orders_router
from sut.app.routers.products import router as products_router

__all__ = [
    "admin_router",
    "auth_router",
    "coupons_router",
    "orders_router",
    "products_router",
]
