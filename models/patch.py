"""Patch data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FileChange(BaseModel):
    """A single file change in a patch."""
    path: str = Field(..., description="Relative file path")
    action: str = Field(..., description="modify, add, or delete")
    additions: int = Field(default=0)
    deletions: int = Field(default=0)
    hunks: List[str] = Field(default_factory=list, description="Diff hunks for this file")


class PatchCreate(BaseModel):
    """Schema for creating a patch."""
    incident_id: UUID
    diff: str = Field(..., description="Unified diff content")
    reasoning: str = Field(..., description="Root cause explanation")
    confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made by Reasoner")
    token_usage: Optional[Dict[str, int]] = Field(default=None, description="LLM token usage")


class Patch(BaseModel):
    """Full patch model."""
    id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    diff: str = Field(..., description="Unified diff content")
    reasoning: str = Field(..., description="Root cause explanation in markdown")
    confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: List[str] = Field(default_factory=list)
    files_changed: List[FileChange] = Field(default_factory=list)
    verified: bool = Field(default=False)
    verification_id: Optional[UUID] = Field(default=None)
    token_usage: Optional[Dict[str, int]] = Field(default=None)
    retry_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_changes(self) -> int:
        """Total number of line changes."""
        return sum(f.additions + f.deletions for f in self.files_changed)
    
    @property
    def summary(self) -> str:
        """Brief summary of changes."""
        if not self.files_changed:
            return "No files changed"
        file_count = len(self.files_changed)
        additions = sum(f.additions for f in self.files_changed)
        deletions = sum(f.deletions for f in self.files_changed)
        return f"{file_count} file(s), +{additions}/-{deletions}"

    class Config:
        """Pydantic config."""
        from_attributes = True


class PatchResponse(BaseModel):
    """API response schema for patch."""
    id: UUID
    incident_id: UUID
    diff: str
    reasoning: str
    confidence: float
    assumptions: List[str]
    files_changed: List[FileChange]
    verified: bool
    summary: str
    created_at: datetime


class ReasonerOutput(BaseModel):
    """Output from the Reasoner agent."""
    incident_id: UUID
    patch: Patch
    root_cause_summary: str = Field(..., description="One-line root cause summary")
    detailed_explanation: str = Field(..., description="Full markdown explanation")
    confidence: float = Field(..., ge=0.0, le=1.0)
    assumptions: List[str] = Field(default_factory=list)
    alternative_fixes: List[str] = Field(default_factory=list, description="Other possible fixes")
    risk_assessment: str = Field(default="", description="Potential risks of this fix")
    token_usage: Dict[str, int] = Field(default_factory=dict)
    llm_model: str = Field(default="")
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
