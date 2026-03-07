"""Coupon management routes (admin only)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.auth.dependencies import AdminUser
from sut.app.database import get_db
from sut.app.schemas.coupon import CouponCreate, CouponResponse
from sut.app.services import coupon_service

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.post("", response_model=CouponResponse, status_code=201)
async def create_coupon(
    data: CouponCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: AdminUser,
) -> CouponResponse:
    coupon = await coupon_service.create_coupon(db, data)
    return CouponResponse.model_validate(coupon)


@router.get("", response_model=list[CouponResponse])
async def list_coupons(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[CouponResponse]:
    coupons = await coupon_service.list_coupons(db, skip=skip, limit=limit)
    return [CouponResponse.model_validate(c) for c in coupons]


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: AdminUser,
) -> CouponResponse:
    coupon = await coupon_service.get_coupon(db, coupon_id)
    if coupon is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    return CouponResponse.model_validate(coupon)
