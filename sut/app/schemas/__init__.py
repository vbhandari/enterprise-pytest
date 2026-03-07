"""Pydantic request/response schemas."""

from sut.app.schemas.auth import LoginRequest, TokenPayload, TokenResponse
from sut.app.schemas.coupon import CouponCreate, CouponResponse
from sut.app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from sut.app.schemas.order import (
    ApplyCouponRequest,
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from sut.app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

__all__ = [
    "ApplyCouponRequest",
    "CouponCreate",
    "CouponResponse",
    "CustomerCreate",
    "CustomerResponse",
    "CustomerUpdate",
    "LoginRequest",
    "OrderCreate",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderListResponse",
    "OrderResponse",
    "OrderStatusUpdate",
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "TokenPayload",
    "TokenResponse",
]
