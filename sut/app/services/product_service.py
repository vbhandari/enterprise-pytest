"""Product business logic."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.models.product import Product
from sut.app.schemas.product import ProductCreate, ProductUpdate


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    """Create a new product."""
    product = Product(**data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    """Get a product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def list_products(
    db: AsyncSession,
    *,
    category: str | None = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> list[Product]:
    """List products with optional filtering."""
    query = select(Product).where(Product.is_active == is_active)
    if category:
        query = query.where(Product.category == category)
    query = query.offset(skip).limit(limit).order_by(Product.id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_product(
    db: AsyncSession, product_id: int, data: ProductUpdate
) -> Product | None:
    """Update an existing product."""
    product = await get_product(db, product_id)
    if product is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """Soft-delete a product by marking it inactive."""
    product = await get_product(db, product_id)
    if product is None:
        return False
    product.is_active = False
    await db.flush()
    return True
