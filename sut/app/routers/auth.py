"""Authentication routes — register and login."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.database import get_db
from sut.app.schemas.auth import LoginRequest, TokenResponse
from sut.app.schemas.customer import CustomerCreate, CustomerResponse
from sut.app.services import customer_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CustomerResponse, status_code=201)
async def register(
    data: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CustomerResponse:
    customer = await customer_service.register_customer(db, data)
    return CustomerResponse.model_validate(customer)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    return await customer_service.authenticate_customer(db, data.email, data.password)
