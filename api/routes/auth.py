from typing import Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from config.logging_config import get_logger
from config.settings import get_settings

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/test")
async def test_route():
    """Test endpoint to verify router is registered."""
    return {"status": "auth router working"}


@router.get("/github/login")
async def github_login(request: Request):
    """Initiate GitHub OAuth flow."""
    client_id = settings.GITHUB_CLIENT_ID
    if not client_id:
        logger.error("GitHub Client ID not configured")
        raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
    
    # Generate random state for CSRF protection
    state = str(uuid4())
    
    # Scopes: repo (Full control of private repositories), user (Read user data)
    scopes = "repo,user"
    
    redirect_uri = f"{request.base_url}api/v1/auth/github/callback"
    logger.info("Initiating GitHub OAuth", redirect_uri=redirect_uri)
    
    # Construct authorization URL
    auth_url = (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&state={state}"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(code: str, state: str, request: Request):
    """Handle GitHub OAuth callback."""
    logger.info("Received GitHub callback", code=code[:8] + "...")
    
    client_id = settings.GITHUB_CLIENT_ID
    client_secret = settings.GITHUB_CLIENT_SECRET
    
    if not client_id or not client_secret:
        logger.error("GitHub Credentials not configured in callback")
        raise HTTPException(status_code=500, detail="GitHub Credentials not configured")
        
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        # Request access token
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret.get_secret_value(),
                "code": code,
                "redirect_uri": f"{str(request.base_url)}api/v1/auth/github/callback",
                "state": state,
            },
        )
        
        if token_response.status_code != 200:
            logger.error("Failed to get access token", response=token_response.text)
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")
            
        token_data = token_response.json()
        if "error" in token_data:
            logger.error("GitHub token error", error=token_data)
            raise HTTPException(status_code=400, detail=f"GitHub Error: {token_data.get('error_description')}")

        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("No access token in response", response=token_data)
            raise HTTPException(status_code=400, detail="No access token returned")
            
        # Get user info (optional, just to confirm connection)
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        
        username = "unknown"
        if user_response.status_code == 200:
            user_data = user_response.json()
            username = user_data.get("login")
            logger.info("GitHub user connected", username=username)
        else:
            logger.warning("Failed to get user info", status=user_response.status_code)
            
    # Redirect to frontend with token
    frontend_url = "http://localhost:3000"  # Assuming frontend port
    return RedirectResponse(url=f"{frontend_url}?token={access_token}&username={username}")
