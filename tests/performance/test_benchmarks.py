"""Service-layer micro-benchmarks using pytest-benchmark."""

from __future__ import annotations

import pytest

from sut.app.auth.passwords import hash_password, verify_password
from sut.app.models.order import OrderStatus
from sut.app.schemas.order import OrderCreate
from sut.app.schemas.product import ProductCreate, ProductResponse

pytestmark = [pytest.mark.performance]


class TestPasswordBenchmarks:
    """Benchmark password hashing operations."""

    def test_hash_password(self, benchmark) -> None:
        benchmark(hash_password, "BenchmarkPass123!")

    def test_verify_password(self, benchmark) -> None:
        hashed = hash_password("BenchmarkPass123!")
        benchmark(verify_password, "BenchmarkPass123!", hashed)


class TestSchemaBenchmarks:
    """Benchmark Pydantic model serialization/deserialization."""

    def test_product_create_validation(self, benchmark) -> None:
        data = {
            "name": "Benchmark Widget",
            "description": "A widget for benchmarking",
            "price": 29.99,
            "stock_quantity": 100,
            "category": "electronics",
        }
        benchmark(ProductCreate.model_validate, data)

    def test_product_response_serialization(self, benchmark) -> None:
        from datetime import UTC, datetime

        product = ProductResponse(
            id=1,
            name="Widget",
            description="desc",
            price=29.99,
            stock_quantity=100,
            category="electronics",
            is_active=True,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        benchmark(product.model_dump_json)

    def test_order_create_validation(self, benchmark) -> None:
        data = {
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1},
                {"product_id": 3, "quantity": 5},
            ]
        }
        benchmark(OrderCreate.model_validate, data)


class TestOrderStateMachineBenchmarks:
    """Benchmark order state machine logic."""

    def test_valid_transition_check(self, benchmark) -> None:
        status = OrderStatus.CREATED
        benchmark(status.can_transition_to, OrderStatus.PAID)

    def test_invalid_transition_check(self, benchmark) -> None:
        status = OrderStatus.CREATED
        benchmark(status.can_transition_to, OrderStatus.DELIVERED)

    def test_all_transitions_lookup(self, benchmark) -> None:
        benchmark(OrderStatus.valid_transitions)
