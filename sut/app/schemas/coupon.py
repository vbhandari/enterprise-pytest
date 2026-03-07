"""Pydantic schemas for Coupon operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class CouponBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    discount_percent: float = Field(..., gt=0, le=100)
    valid_from: datetime
    valid_to: datetime
    max_uses: int = Field(default=100, gt=0)


class CouponCreate(CouponBase):
    pass


class CouponResponse(CouponBase):
    id: int
    current_uses: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
