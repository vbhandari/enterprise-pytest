"""
Locust load test for the Order Management API.

Simulates realistic user flows:
- Browse products
- Register / login
- Create orders
- View order history

Run with::

    locust -f tests/performance/locustfile.py --host http://localhost:8000
"""

from __future__ import annotations

import random

from locust import HttpUser, between, task


class BrowsingUser(HttpUser):
    """Simulates a user browsing products and checking health."""

    weight = 3
    wait_time = between(1, 3)

    @task(5)
    def list_products(self) -> None:
        self.client.get("/products")

    @task(2)
    def get_product(self) -> None:
        self.client.get(f"/products/{random.randint(1, 10)}")

    @task(1)
    def health_check(self) -> None:
        self.client.get("/health")


class ShoppingUser(HttpUser):
    """Simulates a customer who registers, logs in, and places orders."""

    weight = 1
    wait_time = between(2, 5)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.token: str | None = None
        self._user_id = random.randint(100000, 999999)

    def on_start(self) -> None:
        """Register and login at the start of each simulated user session."""
        email = f"locust_{self._user_id}@test.com"
        password = "LocustPass123!"

        self.client.post(
            "/auth/register",
            json={"name": f"Locust User {self._user_id}", "email": email, "password": password},
        )
        resp = self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @property
    def _auth_headers(self) -> dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(3)
    def browse_products(self) -> None:
        self.client.get("/products")

    @task(2)
    def create_order(self) -> None:
        if not self.token:
            return
        product_id = random.randint(1, 5)
        quantity = random.randint(1, 3)
        self.client.post(
            "/orders",
            json={"items": [{"product_id": product_id, "quantity": quantity}]},
            headers=self._auth_headers,
        )

    @task(1)
    def view_orders(self) -> None:
        if not self.token:
            return
        self.client.get("/orders", headers=self._auth_headers)
