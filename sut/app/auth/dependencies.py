"""FastAPI auth dependencies for route protection."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sut.app.auth.jwt import decode_access_token
from sut.app.database import get_db
from sut.app.models.customer import Customer

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Customer:
    """Extract and validate the current user from the JWT bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as e:
        raise credentials_exception from e

    user_id: int = payload["sub"]  # type: ignore[assignment]
    result = await db.execute(select(Customer).where(Customer.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def require_admin(
    current_user: Annotated[Customer, Depends(get_current_user)],
) -> Customer:
    """Require that the current user has the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


CurrentUser = Annotated[Customer, Depends(get_current_user)]
AdminUser = Annotated[Customer, Depends(require_admin)]
