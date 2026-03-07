"""Order and OrderItem ORM models."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sut.app.database import Base

if TYPE_CHECKING:
    from sut.app.models.customer import Customer


class OrderStatus(StrEnum):
    """Valid order statuses forming a state machine."""

    CREATED = "created"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

    @classmethod
    def valid_transitions(cls) -> dict["OrderStatus", list["OrderStatus"]]:
        """Return the allowed state transitions."""
        return {
            cls.CREATED: [cls.PAID, cls.CANCELLED],
            cls.PAID: [cls.SHIPPED, cls.CANCELLED],
            cls.SHIPPED: [cls.DELIVERED],
            cls.DELIVERED: [],
            cls.CANCELLED: [],
        }

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """Check if transitioning to new_status is valid."""
        return new_status in self.valid_transitions().get(self, [])


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")

    @property
    def subtotal(self) -> float:
        return round(float(self.unit_price) * self.quantity, 2)

    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.id}, product_id={self.product_id}, "
            f"qty={self.quantity}, unit_price={self.unit_price})>"
        )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OrderStatus.CREATED
    )
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def status_enum(self) -> OrderStatus:
        return OrderStatus(self.status)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, status='{self.status}', total={self.total})>"
