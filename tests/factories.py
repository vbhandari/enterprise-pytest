"""
Test data factories and builders.

Uses factory_boy for model factories and a custom builder pattern
for complex multi-entity test scenarios.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import factory
from faker import Faker

fake = Faker()

# ---------------------------------------------------------------------------
# Default test password
# ---------------------------------------------------------------------------

DEFAULT_PASSWORD = "TestPass123!"


# ---------------------------------------------------------------------------
# factory_boy factories  (dict-based — no ORM session coupling)
# ---------------------------------------------------------------------------


class CustomerFactory(factory.Factory):
    """Generate customer data dicts for API requests or direct DB inserts."""

    class Meta:
        model = dict
        exclude = ("_seq",)

    _seq = factory.Sequence(lambda n: n)

    name = factory.LazyAttribute(lambda o: fake.name())
    email = factory.LazyAttribute(lambda o: f"user{o._seq}@test.com")
    password = DEFAULT_PASSWORD
    role = "customer"


class AdminFactory(CustomerFactory):
    """Customer factory defaulting to admin role."""

    name = factory.LazyAttribute(lambda o: f"Admin {fake.last_name()}")
    email = factory.LazyAttribute(lambda o: f"admin{o._seq}@test.com")
    role = "admin"


class ProductFactory(factory.Factory):
    """Generate product data dicts."""

    class Meta:
        model = dict

    name = factory.LazyAttribute(lambda _: fake.catch_phrase())
    description = factory.LazyAttribute(lambda _: fake.sentence(nb_words=10))
    price = factory.LazyAttribute(
        lambda _: round(fake.pyfloat(min_value=1.0, max_value=999.99, right_digits=2), 2)
    )
    stock_quantity = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=500))
    category = factory.LazyAttribute(
        lambda _: fake.random_element(["electronics", "clothing", "books", "home", "sports"])
    )


class CouponFactory(factory.Factory):
    """Generate coupon data dicts."""

    class Meta:
        model = dict
        exclude = ("_seq",)

    _seq = factory.Sequence(lambda n: n)

    code = factory.LazyAttribute(lambda o: f"SAVE{o._seq:04d}")
    discount_percent = factory.LazyAttribute(
        lambda _: round(fake.pyfloat(min_value=5.0, max_value=50.0, right_digits=2), 2)
    )
    valid_from = factory.LazyFunction(lambda: datetime.now(tz=UTC).isoformat())
    valid_to = factory.LazyFunction(lambda: (datetime.now(tz=UTC) + timedelta(days=30)).isoformat())
    max_uses = 100


class OrderItemFactory(factory.Factory):
    """Generate order item data dicts (for order creation requests)."""

    class Meta:
        model = dict

    product_id = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=100))
    quantity = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=5))


# ---------------------------------------------------------------------------
# Builder pattern for complex test scenarios
# ---------------------------------------------------------------------------


class OrderBuilder:
    """
    Fluent builder for constructing complex order test scenarios.

    Usage::

        scenario = (
            OrderBuilder()
            .with_items(3, price=29.99, quantity=2)
            .with_coupon("SAVE10", discount_percent=10)
            .with_customer(role="admin")
            .build()
        )

    The builder returns a dict with all the data needed to set up
    the scenario via API calls.
    """

    def __init__(self) -> None:
        self._customer_data: dict[str, Any] = CustomerFactory()
        self._product_overrides: list[dict[str, Any]] = []
        self._item_count: int = 1
        self._item_overrides: dict[str, Any] = {}
        self._coupon_data: dict[str, Any] | None = None
        self._status_chain: list[str] = []

    def with_customer(self, **overrides: Any) -> OrderBuilder:
        """Customize the customer for this order."""
        self._customer_data = CustomerFactory(**overrides)
        return self

    def with_admin_customer(self) -> OrderBuilder:
        """Use an admin customer."""
        self._customer_data = AdminFactory()
        return self

    def with_items(
        self,
        count: int = 1,
        *,
        price: float | None = None,
        quantity: int | None = None,
        stock: int | None = None,
    ) -> OrderBuilder:
        """Configure the number of line items and optionally fix price/qty."""
        self._item_count = count
        if price is not None:
            self._item_overrides["price"] = price
        if quantity is not None:
            self._item_overrides["quantity"] = quantity
        if stock is not None:
            self._item_overrides["stock_quantity"] = stock
        return self

    def with_products(self, products: list[dict[str, Any]]) -> OrderBuilder:
        """Supply explicit product data instead of generating."""
        self._product_overrides = products
        return self

    def with_coupon(self, code: str | None = None, **overrides: Any) -> OrderBuilder:
        """Add a coupon to this order scenario."""
        if code:
            overrides["code"] = code
        self._coupon_data = CouponFactory(**overrides)
        return self

    def with_status_chain(self, *statuses: str) -> OrderBuilder:
        """
        Define the sequence of status transitions to apply after creation.

        Example: ``with_status_chain("paid", "shipped")``
        """
        self._status_chain = list(statuses)
        return self

    def build(self) -> dict[str, Any]:
        """
        Return a dict describing the full scenario.

        Keys:
            customer: dict for registration
            products: list of product dicts for creation
            order_items: list of {product_index, quantity} for order creation
            coupon: optional coupon dict
            status_chain: list of statuses to transition through
        """
        # Generate products
        products: list[dict[str, Any]]
        if self._product_overrides:
            products = self._product_overrides
        else:
            products = []
            for _ in range(self._item_count):
                overrides: dict[str, Any] = {}
                if "price" in self._item_overrides:
                    overrides["price"] = self._item_overrides["price"]
                if "stock_quantity" in self._item_overrides:
                    overrides["stock_quantity"] = self._item_overrides["stock_quantity"]
                else:
                    qty = self._item_overrides.get("quantity", 2)
                    overrides["stock_quantity"] = qty + 10
                products.append(ProductFactory(**overrides))

        # Generate order items (product_index maps to position in products list)
        order_items = []
        for i in range(self._item_count):
            qty = self._item_overrides.get("quantity", 1)
            order_items.append({"product_index": i, "quantity": qty})

        return {
            "customer": self._customer_data,
            "products": products,
            "order_items": order_items,
            "coupon": self._coupon_data,
            "status_chain": self._status_chain,
        }
