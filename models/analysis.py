"""Analysis result models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """Categories of failure types."""
    LOGIC_ERROR = "logic_error"
    DATABASE_QUERY = "database_query"
    TIMEOUT = "timeout"
    CONFIG_MISMATCH = "config_mismatch"
    DEPENDENCY_VERSION = "dependency_version"
    TYPE_ERROR = "type_error"
    NAME_ERROR = "name_error"
    IMPORT_ERROR = "import_error"
    SYNTAX_ERROR = "syntax_error"
    PERMISSION_ERROR = "permission_error"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


class SuspectedFile(BaseModel):
    """A file suspected to contain the bug."""
    path: str = Field(..., description="Relative file path in repo")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    line_numbers: List[int] = Field(default_factory=list, description="Suspected line numbers")
    snippet: Optional[str] = Field(default=None, description="Relevant code snippet")
    evidence: List[str] = Field(default_factory=list, description="Evidence for suspicion")


class SuspectedFunction(BaseModel):
    """A function/method suspected to contain the bug."""
    name: str = Field(..., description="Function or method name")
    file_path: str = Field(..., description="File containing the function")
    start_line: int = Field(..., description="Starting line number")
    end_line: Optional[int] = Field(default=None, description="Ending line number")
    confidence: float = Field(..., ge=0.0, le=1.0)


class ErrorInfo(BaseModel):
    """Extracted error information from logs."""
    error_type: str = Field(..., description="Exception/error type name")
    message: str = Field(..., description="Error message")
    file_path: Optional[str] = Field(default=None, description="File where error occurred")
    line_number: Optional[int] = Field(default=None, description="Line number")
    stack_trace: Optional[str] = Field(default=None, description="Full stack trace")


class RecentChange(BaseModel):
    """A recent git change that might be related."""
    commit_sha: str = Field(..., description="Commit SHA")
    author: str = Field(..., description="Commit author")
    message: str = Field(..., description="Commit message")
    timestamp: datetime
    files_changed: List[str] = Field(default_factory=list)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DetectiveReport(BaseModel):
    """Output from the Detective agent."""
    incident_id: UUID
    errors: List[ErrorInfo] = Field(default_factory=list)
    failure_category: FailureCategory = FailureCategory.UNKNOWN
    suspected_files: List[SuspectedFile] = Field(default_factory=list)
    suspected_functions: List[SuspectedFunction] = Field(default_factory=list)
    recent_changes: List[RecentChange] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence citations")
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    analysis_duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def top_suspect(self) -> Optional[SuspectedFile]:
        """Get the highest confidence suspect."""
        if not self.suspected_files:
            return None
        return max(self.suspected_files, key=lambda f: f.confidence)


class SanitizationEntry(BaseModel):
    """A single sanitized secret entry."""
    file_path: str
    line_number: int
    secret_type: str
    placeholder: str
    severity: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SanitizationReport(BaseModel):
    """Output from the Sanitizer agent."""
    incident_id: UUID
    sanitized_repo_path: str = Field(..., description="Path to sanitized shadow repo")
    total_files_scanned: int = Field(default=0)
    total_secrets_found: int = Field(default=0)
    entries: List[SanitizationEntry] = Field(default_factory=list)
    high_entropy_detections: int = Field(default=0)
    pattern_matches: int = Field(default=0)
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
    halted: bool = Field(default=False, description="Whether processing was halted due to too many secrets")
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Analysis(BaseModel):
    """Combined analysis record for database storage."""
    id: UUID = Field(default_factory=uuid4)
    incident_id: UUID
    agent: str = Field(..., description="Agent name: sanitizer, detective, reasoner, surgeon")
    output: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""
        from_attributes = True
