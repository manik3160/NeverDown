"""Pull request data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PRStatus(str, Enum):
    """Status of pull request."""
    DRAFT = "draft"
    OPEN = "open"
    MERGED = "merged"
    CLOSED = "closed"
    PENDING = "pending"  # Not yet created


# Alias for compatibility
PullRequestStatus = PRStatus


class PRLabel(BaseModel):
    """GitHub label."""
    name: str
    color: str = Field(default="0366d6")
    description: Optional[str] = None


class PRCreate(BaseModel):
    """Schema for creating a PR record."""
    incident_id: UUID
    patch_id: UUID
    verification_id: UUID


class PullRequest(BaseModel):
    """Full pull request model."""
    id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    patch_id: UUID
    verification_id: UUID
    
    # GitHub data
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    branch_name: Optional[str] = None
    base_branch: str = Field(default="main")
    
    # PR content
    title: str = Field(default="")
    body: str = Field(default="")
    labels: List[str] = Field(default_factory=lambda: ["neverdown", "automated-fix", "needs-review"])
    
    # Status
    status: PRStatus = PRStatus.PENDING
    merge_commit_sha: Optional[str] = None
    
    # API response data
    github_response: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    @property
    def is_open(self) -> bool:
        """Check if PR is open."""
        return self.status in (PRStatus.OPEN, PRStatus.DRAFT)

    class Config:
        """Pydantic config."""
        from_attributes = True


class PullRequestResponse(BaseModel):
    """API response schema for PR."""
    id: UUID
    incident_id: UUID
    patch_id: UUID
    pr_number: Optional[int]
    pr_url: Optional[str]
    branch_name: Optional[str]
    title: str
    status: PRStatus
    labels: List[str]
    created_at: datetime
    merged_at: Optional[datetime]


class PRManagerOutput(BaseModel):
    """Output from the PR Manager agent."""
    incident_id: UUID
    patch_id: UUID
    pull_request: PullRequest
    branch_created: bool = Field(default=False)
    patch_applied: bool = Field(default=False)
    committed: bool = Field(default=False)
    pushed: bool = Field(default=False)
    pr_created: bool = Field(default=False)
    commit_sha: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
