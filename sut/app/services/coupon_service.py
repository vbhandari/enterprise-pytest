"""Coupon business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.models.coupon import Coupon
from sut.app.schemas.coupon import CouponCreate


async def create_coupon(db: AsyncSession, data: CouponCreate) -> Coupon:
    """Create a new coupon."""
    coupon = Coupon(**data.model_dump())
    db.add(coupon)
    await db.flush()
    await db.refresh(coupon)
    return coupon


async def get_coupon(db: AsyncSession, coupon_id: int) -> Coupon | None:
    """Get a coupon by ID."""
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    return result.scalar_one_or_none()


async def get_coupon_by_code(db: AsyncSession, code: str) -> Coupon | None:
    """Get a coupon by its code."""
    result = await db.execute(select(Coupon).where(Coupon.code == code))
    return result.scalar_one_or_none()


async def list_coupons(
    db: AsyncSession,
    *,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> list[Coupon]:
    """List coupons with optional filtering."""
    query = (
        select(Coupon)
        .where(Coupon.is_active == is_active)
        .offset(skip)
        .limit(limit)
        .order_by(Coupon.id)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
