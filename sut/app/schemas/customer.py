"""Pydantic schemas for Customer operations."""

from datetime import datetime

from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)


class CustomerCreate(CustomerBase):
    password: str = Field(..., min_length=8, max_length=128)


class CustomerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, min_length=3, max_length=255)
    is_active: bool | None = None


class CustomerResponse(CustomerBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
