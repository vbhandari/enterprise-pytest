"""Pydantic schemas for Order operations."""

from datetime import datetime

from pydantic import BaseModel, Field

from sut.app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class ApplyCouponRequest(BaseModel):
    coupon_code: str = Field(..., min_length=1, max_length=50)


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    total: float
    discount_code: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    total: float
    created_at: datetime

    model_config = {"from_attributes": True}
