"""
Property-based tests for Pydantic schema validation.

Uses Hypothesis to generate random inputs and verify that schema
validation is consistent — valid inputs always parse, invalid inputs
always raise, and round-trips preserve data.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from sut.app.models.order import OrderStatus
from sut.app.schemas.customer import CustomerCreate
from sut.app.schemas.order import OrderCreate, OrderItemCreate
from sut.app.schemas.product import ProductCreate

pytestmark = [pytest.mark.hypothesis]


# ---------------------------------------------------------------------------
# Custom strategies
# ---------------------------------------------------------------------------

valid_product_names = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
        whitelist_characters="-_&' ",
    ),
    min_size=1,
    max_size=200,
).filter(lambda s: s.strip())

valid_prices = st.floats(min_value=0.01, max_value=999999.99, allow_nan=False, allow_infinity=False)
valid_stock = st.integers(min_value=0, max_value=1_000_000)
valid_categories = st.sampled_from(
    ["electronics", "clothing", "books", "home", "sports", "food", "general"]
)


# ---------------------------------------------------------------------------
# Schema property tests
# ---------------------------------------------------------------------------


class TestProductCreateProperties:
    """Property-based tests for ProductCreate schema."""

    @given(
        name=valid_product_names,
        price=valid_prices,
        stock=valid_stock,
        category=valid_categories,
    )
    @settings(max_examples=50)
    def test_valid_products_always_parse(
        self, name: str, price: float, stock: int, category: str
    ) -> None:
        """Any product with valid ranges should successfully validate."""
        product = ProductCreate(
            name=name,
            price=round(price, 2),
            stock_quantity=stock,
            category=category,
        )
        assert product.name == name
        assert product.price == round(price, 2)
        assert product.stock_quantity == stock

    @given(
        price=st.one_of(
            st.floats(max_value=0, allow_nan=False, allow_infinity=False),
            st.just(float("nan")),
        )
    )
    @settings(max_examples=30)
    def test_invalid_prices_always_rejected(self, price: float) -> None:
        """Zero, negative, and NaN prices should all be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductCreate(
                name="Test",
                price=price,
                stock_quantity=10,
                category="general",
            )

    @given(name=st.text(min_size=201, max_size=300))
    @settings(max_examples=20)
    def test_overlong_names_rejected(self, name: str) -> None:
        """Names exceeding 200 chars should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProductCreate(
                name=name,
                price=10.00,
                stock_quantity=5,
                category="general",
            )


class TestOrderCreateProperties:
    """Property-based tests for OrderCreate schema."""

    @given(
        items=st.lists(
            st.builds(
                OrderItemCreate,
                product_id=st.integers(min_value=1, max_value=10000),
                quantity=st.integers(min_value=1, max_value=100),
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=50)
    def test_valid_orders_always_parse(self, items: list[OrderItemCreate]) -> None:
        """Orders with at least one valid item should parse."""
        order = OrderCreate(items=items)
        assert len(order.items) == len(items)
        for item in order.items:
            assert item.quantity > 0
            assert item.product_id > 0

    @given(
        quantity=st.integers(max_value=0),
    )
    @settings(max_examples=20)
    def test_zero_or_negative_quantity_rejected(self, quantity: int) -> None:
        """Zero or negative quantities must fail validation."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OrderCreate(
                items=[OrderItemCreate(product_id=1, quantity=quantity)]
            )

    def test_empty_items_rejected(self) -> None:
        """An order with no items should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            OrderCreate(items=[])


class TestCustomerCreateProperties:
    """Property-based tests for CustomerCreate schema."""

    @given(
        name=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
        email=st.emails(),
        password=st.text(min_size=8, max_size=128).filter(lambda s: s.strip()),
    )
    @settings(max_examples=50)
    def test_valid_customers_parse(
        self, name: str, email: str, password: str
    ) -> None:
        """Valid name/email/password combos should always validate."""
        customer = CustomerCreate(name=name, email=email, password=password)
        assert customer.name == name
        assert customer.email == email

    @given(password=st.text(max_size=7))
    @settings(max_examples=20)
    def test_short_passwords_rejected(self, password: str) -> None:
        """Passwords under 8 chars should be rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CustomerCreate(
                name="Test User",
                email="test@example.com",
                password=password,
            )


class TestOrderStatusStateMachine:
    """Property-based tests for order status transition logic."""

    @given(status=st.sampled_from(list(OrderStatus)))
    @settings(max_examples=20)
    def test_terminal_states_have_no_transitions(self, status: OrderStatus) -> None:
        """DELIVERED and CANCELLED should have no valid outgoing transitions."""
        transitions = OrderStatus.valid_transitions()
        if status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            assert transitions[status] == []

    @given(status=st.sampled_from(list(OrderStatus)))
    @settings(max_examples=20)
    def test_transition_consistency(self, status: OrderStatus) -> None:
        """If A->B is valid, B should exist in the enum."""
        transitions = OrderStatus.valid_transitions()
        for target in transitions.get(status, []):
            assert isinstance(target, OrderStatus)

    @given(
        from_status=st.sampled_from(list(OrderStatus)),
        to_status=st.sampled_from(list(OrderStatus)),
    )
    @settings(max_examples=50)
    def test_can_transition_matches_lookup(
        self, from_status: OrderStatus, to_status: OrderStatus
    ) -> None:
        """can_transition_to should agree with the transitions dict."""
        transitions = OrderStatus.valid_transitions()
        expected = to_status in transitions.get(from_status, [])
        assert from_status.can_transition_to(to_status) == expected
