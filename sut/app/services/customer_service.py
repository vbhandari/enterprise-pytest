"""Customer and authentication business logic."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.auth.jwt import create_access_token
from sut.app.auth.passwords import hash_password, verify_password
from sut.app.models.customer import Customer
from sut.app.schemas.auth import TokenResponse
from sut.app.schemas.customer import CustomerCreate


async def register_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    """Register a new customer account."""
    # Check for existing email
    result = await db.execute(select(Customer).where(Customer.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    customer = Customer(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="customer",
    )
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return customer


async def authenticate_customer(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """Authenticate a customer and return a JWT token."""
    result = await db.execute(
        select(Customer).where(Customer.email == email, Customer.is_active == True)  # noqa: E712
    )
    customer = result.scalar_one_or_none()

    if customer is None or not verify_password(password, customer.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=customer.id, role=customer.role)
    return TokenResponse(access_token=token)


async def get_customer(db: AsyncSession, customer_id: int) -> Customer | None:
    """Get a customer by ID."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    return result.scalar_one_or_none()
