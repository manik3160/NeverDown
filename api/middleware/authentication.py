"""API key authentication middleware."""

from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from config.settings import get_settings

# API key header definition
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """Verify API key from request header.
    
    Args:
        request: FastAPI request object
        api_key: API key from header
        
    Returns:
        The API key if valid, None if auth is disabled
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    settings = get_settings()
    
    # If no API key is configured, skip auth (development mode)
    if not settings.API_KEY:
        return None
    
    expected_key = settings.API_KEY.get_secret_value()
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


def get_api_key_dependency():
    """Get the API key dependency for protected routes.
    
    Usage:
        @app.get("/protected", dependencies=[Depends(get_api_key_dependency())])
        async def protected_route():
            ...
    """
    return verify_api_key
