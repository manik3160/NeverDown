from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any

from config.settings import get_settings, Settings
from agents.agent_4_publisher.github_client import GitHubClient
from core.exceptions import GitHubAPIError

router = APIRouter(tags=["integrations"])


class ConnectRepoRequest(BaseModel):
    repo_url: str


@router.post("/github/webhook")
async def setup_github_webhook(
    request: ConnectRepoRequest,
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Programmatically setup a GitHub webhook for a target repository.
    The webhook URL is hardcoded to the production NeverDown backend for reliability.
    """
    client = GitHubClient()
    
    try:
        # Parse owner and repo
        owner, repo = client.parse_repo_url(request.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if not settings.GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET is not configured on the backend.")

    secret = settings.GITHUB_WEBHOOK_SECRET.get_secret_value()
    # Hardcoded to production URL as per CTO preference, so GitHub reaches Render.
    webhook_url = "https://neverdown-backend.onrender.com/api/v1/webhooks/github"
    
    try:
        result = await client.create_webhook(
            owner=owner,
            repo=repo,
            webhook_url=webhook_url,
            secret=secret
        )
        return {
            "status": "success",
            "message": f"Webhook successfully configured for {owner}/{repo}",
            "data": result
        }
    except GitHubAPIError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup webhook: {str(e)}")
