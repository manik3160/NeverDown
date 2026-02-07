"""Incident data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Severity levels for incidents."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentSource(str, Enum):
    """Source of incident detection."""
    CI = "ci"
    LOGS = "logs"
    MONITORING = "monitoring"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class IncidentStatus(str, Enum):
    """Status of incident processing."""
    PENDING = "pending"
    PROCESSING = "processing"  # General processing state
    SANITIZING = "sanitizing"
    ANALYZING = "analyzing"
    REASONING = "reasoning"
    VERIFYING = "verifying"
    CREATING_PR = "creating_pr"
    PR_CREATED = "pr_created"  # Successfully created PR
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class RepositoryInfo(BaseModel):
    """Repository information for incident."""
    url: str = Field(..., description="Repository URL (e.g., https://github.com/org/repo)")
    branch: str = Field(default="main", description="Branch to analyze")
    commit: Optional[str] = Field(default=None, description="Specific commit SHA")
    
    @property
    def owner(self) -> str:
        """Extract owner from GitHub URL."""
        parts = self.url.rstrip("/").split("/")
        return parts[-2] if len(parts) >= 2 else ""
    
    @property
    def name(self) -> str:
        """Extract repo name from GitHub URL."""
        parts = self.url.rstrip("/").split("/")
        name = parts[-1] if parts else ""
        return name.replace(".git", "")


class IncidentMetadata(BaseModel):
    """Additional metadata for incident."""
    repository: RepositoryInfo
    triggered_by: Optional[str] = Field(default=None, description="User or system that triggered")
    workflow_name: Optional[str] = Field(default=None, description="CI workflow name if applicable")
    job_url: Optional[str] = Field(default=None, description="Link to failed job")
    alert_id: Optional[str] = Field(default=None, description="External alert ID")
    tags: List[str] = Field(default_factory=list, description="Optional tags for categorization")


class IncidentCreate(BaseModel):
    """Schema for creating a new incident."""
    title: str = Field(..., min_length=1, max_length=500, description="Short incident title")
    description: Optional[str] = Field(default=None, description="Detailed description")
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    source: IncidentSource = Field(default=IncidentSource.MANUAL)
    logs: Optional[str] = Field(default=None, description="Error logs or stack traces")
    metadata: IncidentMetadata


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""
    status: Optional[IncidentStatus] = None
    current_state: Optional[str] = None
    error_message: Optional[str] = None


class TimelineEvent(BaseModel):
    """A single event in the incident timeline."""
    state: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class IncidentResponse(BaseModel):
    """Schema for incident API response."""
    id: UUID
    title: str
    description: Optional[str]
    severity: IncidentSeverity
    source: IncidentSource
    status: IncidentStatus
    current_state: Optional[str]
    error_message: Optional[str]
    pr_url: Optional[str]
    timeline: List[TimelineEvent] = Field(default_factory=list)
    metadata: IncidentMetadata
    created_at: datetime
    updated_at: datetime


class IncidentSummary(BaseModel):
    """Brief summary for listing incidents."""
    id: UUID
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    current_state: Optional[str] = None
    error_message: Optional[str] = None
    metadata: IncidentMetadata
    created_at: datetime


class Incident(BaseModel):
    """Full incident model with all data."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source: IncidentSource = IncidentSource.MANUAL
    status: IncidentStatus = IncidentStatus.PENDING
    current_state: Optional[str] = None
    error_message: Optional[str] = None
    logs: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: IncidentMetadata
    timeline: List[TimelineEvent] = Field(default_factory=list)
    pr_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_timeline_event(self, state: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the timeline."""
        self.timeline.append(TimelineEvent(
            state=state,
            timestamp=datetime.utcnow(),
            details=details,
        ))
        self.current_state = state
        self.updated_at = datetime.utcnow()
    
    def to_response(self) -> IncidentResponse:
        """Convert to API response model."""
        return IncidentResponse(
            id=self.id,
            title=self.title,
            description=self.description,
            severity=self.severity,
            source=self.source,
            status=self.status,
            current_state=self.current_state,
            error_message=self.error_message,
            pr_url=self.pr_url,
            timeline=self.timeline,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    class Config:
        """Pydantic config."""
        from_attributes = True
