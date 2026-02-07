"""GitHub API client for the Publisher agent."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import GitHubAPIError
from models.pull_request import PRLabel, PullRequest, PullRequestStatus

logger = get_logger(__name__)


@dataclass
class CreatePRRequest:
    """Request to create a pull request."""
    title: str
    body: str
    head_branch: str
    base_branch: str
    labels: List[str]
    draft: bool = False


@dataclass
class CreateBranchRequest:
    """Request to create a branch."""
    branch_name: str
    base_sha: str


class GitHubClient:
    """GitHub API client for PR operations.
    
    IMPORTANT: This client is for creating PRs ONLY.
    It NEVER auto-merges PRs (human-in-the-loop requirement).
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with GitHub token.
        
        Args:
            token: GitHub personal access token
        """
        self.settings = get_settings()
        
        if token:
            self._token = token
        elif self.settings.GITHUB_TOKEN:
            self._token = self.settings.GITHUB_TOKEN.get_secret_value()
        else:
            self._token = None
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    async def get_default_branch(
        self,
        owner: str,
        repo: str,
    ) -> str:
        """Get the default branch of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Default branch name (e.g., 'main')
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get repository info: {response.text}",
                    status_code=response.status_code,
                )
            
            data = response.json()
            return data.get("default_branch", "main")
    
    async def get_ref(
        self,
        owner: str,
        repo: str,
        ref: str = "heads/main",
    ) -> str:
        """Get SHA for a git reference.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Reference (e.g., 'heads/main')
            
        Returns:
            SHA of the reference
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/ref/{ref}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get ref: {response.text}",
                    status_code=response.status_code,
                )
            
            data = response.json()
            return data.get("object", {}).get("sha", "")
    
    async def create_branch(
        self,
        owner: str,
        repo: str,
        request: CreateBranchRequest,
    ) -> bool:
        """Create a new branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            request: Branch creation request
            
        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/git/refs"
        
        payload = {
            "ref": f"refs/heads/{request.branch_name}",
            "sha": request.base_sha,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
            )
            
            if response.status_code == 422:
                # Branch already exists
                logger.info("Branch already exists", branch=request.branch_name)
                return True
            
            if response.status_code not in (200, 201):
                raise GitHubAPIError(
                    f"Failed to create branch: {response.text}",
                    status_code=response.status_code,
                )
            
            return True
    
    async def push_file(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        content: str,
        message: str,
    ) -> str:
        """Push or update a file to a branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            file_path: Path to file in repo
            content: File content
            message: Commit message
            
        Returns:
            Commit SHA
        """
        import base64
        
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
        
        # Check if file exists (to get SHA for update)
        sha = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self.headers,
                params={"ref": branch},
            )
            if response.status_code == 200:
                sha = response.json().get("sha")
        
        # Create or update file
        payload: Dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                url,
                headers=self.headers,
                json=payload,
            )
            
            if response.status_code not in (200, 201):
                raise GitHubAPIError(
                    f"Failed to push file: {response.text}",
                    status_code=response.status_code,
                )
            
            return response.json().get("commit", {}).get("sha", "")
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        request: CreatePRRequest,
    ) -> PullRequest:
        """Create a pull request.
        
        IMPORTANT: This creates a PR but does NOT merge it.
        Human review is always required.
        
        Args:
            owner: Repository owner
            repo: Repository name
            request: PR creation request
            
        Returns:
            Created PullRequest
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        
        payload = {
            "title": request.title,
            "body": request.body,
            "head": request.head_branch,
            "base": request.base_branch,
            "draft": request.draft,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
            )
            
            if response.status_code not in (200, 201):
                raise GitHubAPIError(
                    f"Failed to create PR: {response.text}",
                    status_code=response.status_code,
                )
            
            data = response.json()
            
            pr = PullRequest(
                id=data["id"],
                number=data["number"],
                title=data["title"],
                body=data["body"],
                status=PullRequestStatus.OPEN,
                head_branch=request.head_branch,
                base_branch=request.base_branch,
                url=data["html_url"],
            )
            
            # Add labels if specified
            if request.labels:
                await self.add_labels(owner, repo, data["number"], request.labels)
                pr.labels = [PRLabel(name=l) for l in request.labels]
            
            return pr
    
    async def add_labels(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        labels: List[str],
    ) -> None:
        """Add labels to a PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            labels: Labels to add
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{pr_number}/labels"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json={"labels": labels},
            )
            
            if response.status_code not in (200, 201):
                logger.warning(
                    "Failed to add labels",
                    pr_number=pr_number,
                    status=response.status_code,
                )
    
    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> PullRequest:
        """Get a pull request by number.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PullRequest object
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to get PR: {response.text}",
                    status_code=response.status_code,
                )
            
            data = response.json()
            
            status_map = {
                "open": PullRequestStatus.OPEN,
                "closed": PullRequestStatus.CLOSED,
            }
            
            if data.get("merged"):
                status = PullRequestStatus.MERGED
            else:
                status = status_map.get(data["state"], PullRequestStatus.OPEN)
            
            return PullRequest(
                id=data["id"],
                number=data["number"],
                title=data["title"],
                body=data["body"],
                status=status,
                head_branch=data["head"]["ref"],
                base_branch=data["base"]["ref"],
                url=data["html_url"],
                labels=[PRLabel(name=l["name"]) for l in data.get("labels", [])],
            )
    
    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse owner and repo from GitHub URL.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo)
        """
        # Handle various URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/.]+)',
            r'^([^/]+)/([^/]+)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).replace('.git', '')
        
        raise ValueError(f"Could not parse GitHub URL: {url}")
