# enterprise-pytest

Enterprise-grade test architecture combining **Pytest**, **Playwright**, and **Locust** — built around a FastAPI e-commerce Order Management API as the Software Under Test (SUT).

## Overview

This project showcases advanced Python testing patterns at an enterprise level:

- **Functional & regression tests** — Pytest + httpx async client
- **Performance tests** — pytest-benchmark + Locust
- **Messaging tests** — in-memory event broker verification
- **UI tests** — Playwright browser automation
- **Enterprise framework patterns** — custom plugin, layered fixtures, factory-boy data builders, structured logging, parallel execution, retry/stability

## Project Structure

```
enterprise-pytest/
├── sut/                          # Software Under Test
│   └── app/
│       ├── main.py               # FastAPI application factory
│       ├── config.py             # pydantic-settings configuration
│       ├── database.py           # Async SQLAlchemy engine & session
│       ├── auth/                 # JWT, password hashing, dependencies
│       ├── models/               # SQLAlchemy ORM models
│       ├── schemas/              # Pydantic request/response schemas
│       ├── services/             # Business logic layer
│       ├── events/               # In-memory event broker (pub/sub)
│       ├── routers/              # API + admin UI routes
│       ├── templates/            # Jinja2 admin templates
│       └── static/               # CSS assets
├── tests/                        # Test framework (coming soon)
├── pyproject.toml                # Dependencies & tool config
└── README.md
```

## SUT: Order Management API

A self-contained REST API with:

- **Auth** — JWT-based registration & login, role-based access (admin / customer)
- **Products** — CRUD with soft-delete, inventory tracking
- **Orders** — Create → Pay → Ship → Deliver state machine, tax calculation, coupon support
- **Coupons** — Percentage / fixed-amount discounts with expiry and usage limits
- **Events** — In-memory pub/sub broker for order lifecycle events
- **Admin UI** — Server-rendered dashboard with login, order overview, and status filtering

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | SQLite via aiosqlite |
| Auth | python-jose (JWT) + passlib (bcrypt) |
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

## Cross-Platform

The project is OS-agnostic — all filesystem paths use `pathlib.Path`, no platform-specific dependencies.

## License

MIT
