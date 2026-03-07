"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sut.app.config import get_settings
from sut.app.database import Base, engine
from sut.app.routers import auth_router, coupons_router, orders_router, products_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Register API routers
    app.include_router(auth_router)
    app.include_router(products_router)
    app.include_router(orders_router)
    app.include_router(coupons_router)

    # Admin UI router will be added in Step 4

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()
