# enterprise-pytest

Enterprise-grade test architecture combining **Pytest**, **Playwright**, and **Locust** — built around a FastAPI e-commerce Order Management API as the Software Under Test (SUT).

## Overview

This project showcases advanced Python testing patterns at an enterprise level:

- **Functional tests** (10 auth + 7 product + 8 order + 5 coupon) — Pytest + httpx async client
- **Regression tests** (5 order edge-cases + 3 coupon edge-cases + 5 data-integrity) — boundary values, race conditions, previously-fixed bugs
- **Messaging tests** (14 tests) — in-memory event broker verification, subscriber multiplexing
- **Performance tests** — 8 pytest-benchmark micro-benchmarks + Locust load test
- **UI tests** — Playwright browser automation for admin dashboard
- **Enterprise framework patterns** — custom plugin, layered fixtures, factory-boy data builders, structured reporting, parallel execution, retry/stability

**76+ tests** pass out of the box with zero external dependencies.

## Project Structure

```
enterprise-pytest/
├── sut/                              # Software Under Test
│   └── app/
│       ├── main.py                   # FastAPI application factory
│       ├── config.py                 # pydantic-settings configuration
│       ├── database.py               # Async SQLAlchemy engine & session
│       ├── auth/                     # JWT, bcrypt hashing, RBAC dependencies
│       ├── models/                   # SQLAlchemy 2.0 ORM models
│       ├── schemas/                  # Pydantic v2 request/response schemas
│       ├── services/                 # Business logic (orders, products, coupons)
│       ├── events/                   # In-memory event broker (pub/sub)
│       ├── routers/                  # API + admin UI routes
│       ├── templates/                # Jinja2 admin templates
│       └── static/                   # CSS assets
├── tests/                            # Test framework
│   ├── conftest.py                   # Root: layered fixture architecture
│   ├── config.py                     # Environment-aware settings (pydantic-settings)
│   ├── factories.py                  # factory-boy factories + OrderBuilder
│   ├── plugins/
│   │   └── pytest_enterprise.py      # Custom plugin: markers, metadata, hooks
│   ├── utils/
│   │   ├── assertions.py             # Domain assertion helpers (HTTP, orders, events)
│   │   ├── waiters.py                # Async polling helpers (poll_until, wait_for_status)
│   │   └── http_helpers.py           # API shortcut functions (register, create_order, etc.)
│   ├── functional/                   # Feature tests (auth, products, orders, coupons)
│   ├── regression/                   # Edge-case & bug-fix tests
│   ├── messaging/                    # Event broker tests
│   ├── performance/                  # pytest-benchmark + Locust load tests
│   ├── ui/                           # Playwright browser tests
│   ├── test_plugin_smoke.py          # Plugin infrastructure smoke tests
│   └── test_fixtures_smoke.py        # Fixture infrastructure smoke tests
├── .github/workflows/ci.yml          # CI pipeline (lint + test matrix + benchmarks)
├── Makefile                          # Common tasks
├── pyproject.toml                    # Dependencies & tool config
└── README.md
```

## SUT: Order Management API

A self-contained REST API with:

- **Auth** — JWT-based registration & login, role-based access (admin / customer)
- **Products** — CRUD with soft-delete, inventory tracking, category filtering
- **Orders** — Create → Pay → Ship → Deliver state machine, tax calculation, inventory management, coupon support
- **Coupons** — Percentage discounts with date validity, usage limits, and one-per-order constraint
- **Events** — In-memory pub/sub broker publishing `ORDER_CREATED`, `ORDER_PAID`, `ORDER_SHIPPED`, `ORDER_DELIVERED`, `ORDER_CANCELLED`, `INVENTORY_DECREMENTED`, `INVENTORY_RESTORED`, and `ORDER_COUPON_APPLIED`
- **Admin UI** — Server-rendered dashboard with login, order overview, and status filtering

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite via aiosqlite |
| Auth | python-jose (JWT) + bcrypt |
| Validation | Pydantic v2 |
| Config | pydantic-settings |
| Templates | Jinja2 |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/enterprise-pytest.git
cd enterprise-pytest

# Create virtual environment & install
uv venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate          # Windows

uv pip install -e ".[test]"

# Copy environment config (optional — defaults work out of the box)
cp .env.example .env
```

### Run the SUT

```bash
uvicorn sut.app.main:app --reload
```

- **API docs:** http://localhost:8000/docs
- **Admin UI:** http://localhost:8000/admin/login
- **Health check:** http://localhost:8000/health

## Test Framework

### Enterprise Plugin (`tests/plugins/pytest_enterprise.py`)

- **Custom markers** — `@pytest.mark.functional`, `regression`, `performance`, `messaging`, `ui`, `slow`
- **`@test_meta` decorator** — attach traceability metadata (ticket ID, severity, component) to any test
- **`ExchangeStore`** — captures HTTP request/response pairs for debugging and reporting
- **Enriched failure reports** — HTTP exchanges and metadata attached to failed test output
- **Custom terminal summary** — results broken down by component at the end of each run
- **CLI options** — `--test-env local|staging|ci` and `--capture-responses`

### Layered Fixture Architecture (`tests/conftest.py`)

| Scope | Fixture | Purpose |
|-------|---------|---------|
| session | `async_engine` | In-memory SQLite engine shared across all tests |
| session | `session_factory` | Async session maker bound to the test engine |
| session | `app` | FastAPI app with DB dependency overridden |
| function | `db_session` | Per-test session with auto-rollback |
| function | `client` | Unauthenticated `httpx.AsyncClient` |
| function | `admin_client` | Authenticated admin client (DB-seeded) |
| function | `customer_client` | Authenticated customer client (API-registered) |
| function | `exchange_store` | Per-test HTTP exchange capture |
| autouse | `_reset_event_broker` | Clears event history between tests |

### Test Data (`tests/factories.py`)

- **`CustomerFactory`** / **`AdminFactory`** — dict-based user data
- **`ProductFactory`** — randomized product data with Faker
- **`CouponFactory`** — coupon data with configurable validity windows
- **`OrderItemFactory`** — order line items
- **`OrderBuilder`** — fluent builder for complex multi-item order scenarios

### Test Utilities (`tests/utils/`)

- **`assertions.py`** — `assert_status`, `assert_json_keys`, `assert_valid_order_response`, `assert_event_published`, `assert_event_count`
- **`waiters.py`** — `poll_until`, `poll_until_event`, `wait_for_status` for async polling
- **`http_helpers.py`** — `register_customer`, `create_product`, `create_order`, `transition_order`, `create_coupon`, `apply_coupon`

### Test Configuration (`tests/config.py`)

Environment-aware settings via `pydantic-settings` with `TEST_` prefix:

```bash
# Run against staging
TEST_ENV=staging TEST_BASE_URL=https://staging.example.com pytest -m functional
```

### Running Tests

```bash
# All tests (excluding UI and performance)
make test
# or: pytest tests/ -m "not ui and not performance" -v

# By suite
make test-functional          # Feature tests
make test-regression          # Edge-case tests
make test-messaging           # Event broker tests
make test-performance         # pytest-benchmark
make test-ui                  # Playwright (requires: playwright install)
make test-smoke               # Plugin + fixture smoke tests

# By marker
pytest -m functional
pytest -m "regression and not slow"

# With environment
pytest --test-env ci

# Parallel execution
pytest -n auto

# Reporting
make test-html                # HTML report → reports/report.html
make test-allure              # Allure results → reports/allure-results/
make test-junit               # JUnit XML → reports/junit.xml
```

### Performance / Load Testing

```bash
# Micro-benchmarks
make test-performance

# Locust load test (requires running SUT)
make serve                    # Terminal 1
make locust                   # Terminal 2 → http://localhost:8089
```

## CI Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

- **Lint** — Ruff check + format on Ubuntu
- **Test matrix** — Python 3.11 & 3.12 × Ubuntu, macOS, Windows
- **Benchmarks** — pytest-benchmark with JSON artifact upload

## Cross-Platform

The project is OS-agnostic — all filesystem paths use `pathlib.Path`, no platform-specific dependencies. Tested on Linux, macOS, and Windows.

## License

MIT
