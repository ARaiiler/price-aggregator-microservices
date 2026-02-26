"""
Internal API-key authentication.
Only the Node.js gateway possesses the shared secret, so external
clients cannot call the Python collector directly.
"""

import logging
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_API_KEY_HEADER = APIKeyHeader(name="X-Internal-Api-Key", auto_error=False)


async def verify_internal_key(
    api_key: str | None = Security(_API_KEY_HEADER),
) -> str:
    """
    Dependency that rejects requests without a valid internal API key.
    Attach to any route that must remain private.
    """
    if not api_key or api_key != settings.INTERNAL_API_KEY:
        logger.warning("Rejected request – invalid or missing internal API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )
    return api_key
