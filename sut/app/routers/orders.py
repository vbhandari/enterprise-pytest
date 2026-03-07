"""Order routes — CRUD, status transitions, coupon application."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.auth.dependencies import AdminUser, CurrentUser
from sut.app.database import get_db
from sut.app.models.order import OrderStatus
from sut.app.schemas.order import (
    ApplyCouponRequest,
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from sut.app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> OrderResponse:
    order = await order_service.create_order(db, current_user.id, data)
    return OrderResponse.model_validate(order)


@router.get("", response_model=list[OrderListResponse])
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    status_filter: OrderStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[OrderListResponse]:
    # Admins see all orders; customers see only their own
    customer_id = None if current_user.role == "admin" else current_user.id
    orders = await order_service.list_orders(
        db, customer_id=customer_id, status_filter=status_filter, skip=skip, limit=limit
    )
    return [OrderListResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> OrderResponse:
    order = await order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # Customers can only view their own orders
    if current_user.role != "admin" and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: AdminUser,
) -> OrderResponse:
    order = await order_service.update_order_status(db, order_id, data.status)
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/apply-coupon", response_model=OrderResponse)
async def apply_coupon(
    order_id: int,
    data: ApplyCouponRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> OrderResponse:
    # Verify order ownership
    order = await order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role != "admin" and order.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    order = await order_service.apply_coupon(db, order_id, data.coupon_code)
    return OrderResponse.model_validate(order)
