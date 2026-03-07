"""JWT token creation and verification."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from sut.app.config import get_settings


def create_access_token(subject: int, role: str) -> str:
    """Create a JWT access token for the given user ID and role."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, str | int]:
    """Decode and validate a JWT access token. Raises JWTError on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if sub is None or role is None:
            raise JWTError("Missing required claims")
        return {"sub": int(sub), "role": role}
    except (JWTError, ValueError) as e:
        raise JWTError(f"Invalid token: {e}") from e
