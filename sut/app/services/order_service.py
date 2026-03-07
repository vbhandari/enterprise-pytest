"""Order business logic — state machine, inventory, tax, coupons, events."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.config import get_settings
from sut.app.events.broker import Event, EventType, event_broker
from sut.app.models.coupon import Coupon
from sut.app.models.order import Order, OrderItem, OrderStatus
from sut.app.models.product import Product
from sut.app.schemas.order import OrderCreate


def calculate_tax(subtotal: float, discount: float = 0.0) -> float:
    """Calculate tax on the (subtotal - discount) amount."""
    settings = get_settings()
    taxable = max(subtotal - discount, 0.0)
    return round(taxable * settings.tax_rate, 2)


def calculate_order_totals(
    subtotal: float, discount: float = 0.0
) -> dict[str, float]:
    """Return subtotal, discount_amount, tax_amount, and total."""
    tax = calculate_tax(subtotal, discount)
    total = round(subtotal - discount + tax, 2)
    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount, 2),
        "tax_amount": tax,
        "total": total,
    }


async def create_order(
    db: AsyncSession, customer_id: int, data: OrderCreate
) -> Order:
    """
    Create a new order:
    1. Validate products exist and have sufficient stock
    2. Decrement inventory
    3. Calculate totals (subtotal + tax)
    4. Persist order + items
    5. Publish ORDER_CREATED event
    """
    order_items: list[OrderItem] = []
    subtotal = 0.0

    for item_data in data.items:
        result = await db.execute(
            select(Product).where(
                Product.id == item_data.product_id, Product.is_active == True  # noqa: E712
            )
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found or inactive",
            )
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Insufficient stock for product {product.id}: "
                    f"requested {item_data.quantity}, available {product.stock_quantity}"
                ),
            )
        # Decrement inventory
        product.stock_quantity -= item_data.quantity
        line_total = float(product.price) * item_data.quantity
        subtotal += line_total

        order_items.append(
            OrderItem(
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=float(product.price),
            )
        )

    totals = calculate_order_totals(subtotal)

    order = Order(
        customer_id=customer_id,
        status=OrderStatus.CREATED,
        items=order_items,
        **totals,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    # Publish event
    await event_broker.publish(
        Event(
            event_type=EventType.ORDER_CREATED,
            payload={"order_id": order.id, "customer_id": customer_id, "total": totals["total"]},
        )
    )
    # Publish inventory events
    for item in order_items:
        await event_broker.publish(
            Event(
                event_type=EventType.INVENTORY_DECREMENTED,
                payload={"product_id": item.product_id, "quantity": item.quantity},
            )
        )

    return order


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    """Get an order by ID with items eagerly loaded."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    *,
    customer_id: int | None = None,
    status_filter: OrderStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Order]:
    """List orders with optional filtering."""
    query = select(Order)
    if customer_id is not None:
        query = query.where(Order.customer_id == customer_id)
    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Order.id.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_order_status(
    db: AsyncSession, order_id: int, new_status: OrderStatus
) -> Order:
    """
    Transition an order to a new status.
    Validates the transition via the state machine.
    On cancellation, restores inventory.
    """
    order = await get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    current = OrderStatus(order.status)
    if not current.can_transition_to(new_status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot transition from '{current}' to '{new_status}'",
        )

    order.status = new_status

    # Restore inventory on cancellation
    if new_status == OrderStatus.CANCELLED:
        for item in order.items:
            result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = result.scalar_one_or_none()
            if product:
                product.stock_quantity += item.quantity
                await event_broker.publish(
                    Event(
                        event_type=EventType.INVENTORY_RESTORED,
                        payload={"product_id": product.id, "quantity": item.quantity},
                    )
                )

    await db.flush()
    await db.refresh(order)

    # Map status to event type
    status_event_map: dict[OrderStatus, EventType] = {
        OrderStatus.PAID: EventType.ORDER_PAID,
        OrderStatus.SHIPPED: EventType.ORDER_SHIPPED,
        OrderStatus.DELIVERED: EventType.ORDER_DELIVERED,
        OrderStatus.CANCELLED: EventType.ORDER_CANCELLED,
    }
    if event_type := status_event_map.get(new_status):
        await event_broker.publish(
            Event(
                event_type=event_type,
                payload={"order_id": order.id, "new_status": new_status},
            )
        )

    return order


async def apply_coupon(db: AsyncSession, order_id: int, coupon_code: str) -> Order:
    """
    Apply a coupon to an order.
    Validates: order exists & is in CREATED status, coupon is valid, not already applied.
    """
    order = await get_order(db, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    if order.status != OrderStatus.CREATED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coupons can only be applied to orders in 'created' status",
        )

    if order.discount_code is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A coupon has already been applied to this order",
        )

    # Validate coupon
    result = await db.execute(
        select(Coupon).where(Coupon.code == coupon_code, Coupon.is_active == True)  # noqa: E712
    )
    coupon = result.scalar_one_or_none()
    if coupon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{coupon_code}' not found or inactive",
        )

    now = datetime.now(UTC)
    if now < coupon.valid_from or now > coupon.valid_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coupon is not within its validity period",
        )
    if coupon.current_uses >= coupon.max_uses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Coupon has reached its maximum number of uses",
        )

    # Apply discount
    discount = round(float(order.subtotal) * (float(coupon.discount_percent) / 100), 2)
    totals = calculate_order_totals(float(order.subtotal), discount)

    order.discount_code = coupon.code
    order.discount_amount = totals["discount_amount"]
    order.tax_amount = totals["tax_amount"]
    order.total = totals["total"]

    coupon.current_uses += 1

    await db.flush()
    await db.refresh(order)

    await event_broker.publish(
        Event(
            event_type=EventType.ORDER_COUPON_APPLIED,
            payload={
                "order_id": order.id,
                "coupon_code": coupon.code,
                "discount_amount": totals["discount_amount"],
            },
        )
    )

    return order
