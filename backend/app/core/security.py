"""API key authentication dependency."""

from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Validate API key from request header. Skips check when API_KEY is unset."""
    if not settings.API_KEY:
        return ""
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key
