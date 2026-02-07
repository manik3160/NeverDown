"""Verification result models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Status of verification run."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some tests pass, some fail
    ERROR = "error"  # Infrastructure error (not test failure)
    NO_TESTS = "no_tests"  # No tests found or executed


class TestOutcome(str, Enum):
    """Outcome of a single test case."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"  # Test errored (not assertion failure)


class TestResult(BaseModel):
    """Result of a single test."""
    name: str = Field(..., description="Test name/path")
    outcome: TestOutcome = Field(default=TestOutcome.PASSED)
    passed: bool = True  # Backwards compatibility
    duration_ms: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)
    output: Optional[str] = Field(default=None, description="Test output/logs")


class VerificationResult(BaseModel):
    """Result of patch verification."""
    incident_id: UUID
    patch_id: UUID
    status: VerificationStatus = VerificationStatus.PENDING
    tests_passed: int = 0
    tests_failed: int = 0
    tests_run: List[TestResult] = Field(default_factory=list)
    verification_failed_reason: Optional[str] = None
    sandbox_info: Optional[Dict[str, Any]] = None


class SandboxInfo(BaseModel):
    """Information about the sandbox environment."""
    container_id: str = Field(..., description="Docker container ID")
    image: str = Field(..., description="Docker image used")
    network_isolated: bool = Field(default=True)
    memory_limit: str = Field(default="2g")
    started_at: datetime
    stopped_at: Optional[datetime] = None
    exit_code: Optional[int] = None


class VerificationCreate(BaseModel):
    """Schema for creating a verification."""
    patch_id: UUID
    incident_id: UUID


class Verification(BaseModel):
    """Full verification model."""
    id: UUID = Field(default_factory=uuid4)
    patch_id: UUID
    incident_id: UUID
    status: VerificationStatus = VerificationStatus.PENDING
    test_results: List[TestResult] = Field(default_factory=list)
    tests_passed: int = Field(default=0)
    tests_failed: int = Field(default=0)
    tests_skipped: int = Field(default=0)
    sandbox_info: Optional[SandboxInfo] = None
    test_output: str = Field(default="", description="Full stdout/stderr from tests")
    patch_applied_cleanly: bool = Field(default=True)
    health_check_passed: bool = Field(default=False)
    duration_seconds: int = Field(default=0)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def total_tests(self) -> int:
        """Total number of tests run."""
        return self.tests_passed + self.tests_failed + self.tests_skipped
    
    @property
    def success_rate(self) -> float:
        """Percentage of tests that passed."""
        if self.total_tests == 0:
            return 0.0
        return self.tests_passed / self.total_tests
    
    def mark_completed(self, status: VerificationStatus) -> None:
        """Mark verification as completed."""
        self.status = status
        self.completed_at = datetime.utcnow()

    class Config:
        """Pydantic config."""
        from_attributes = True


class VerificationResponse(BaseModel):
    """API response schema for verification."""
    id: UUID
    patch_id: UUID
    incident_id: UUID
    status: VerificationStatus
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    success_rate: float
    patch_applied_cleanly: bool
    health_check_passed: bool
    duration_seconds: int
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class SurgeonOutput(BaseModel):
    """Output from the Surgeon agent."""
    incident_id: UUID
    patch_id: UUID
    verification: Verification
    synthetic_data_count: int = Field(default=0, description="Number of synthetic records generated")
    patch_application_output: str = Field(default="")
    overall_status: VerificationStatus
    recommendation: str = Field(..., description="Proceed to PR, retry, or fail")
    notes: List[str] = Field(default_factory=list)
    duration_ms: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
