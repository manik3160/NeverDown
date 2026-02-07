"""Custom exception hierarchy for NeverDown."""

from typing import Any, Dict, Optional


class NeverDownError(Exception):
    """Base exception for all NeverDown errors."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "NEVERDOWN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# Security Exceptions
# =============================================================================

class SecurityError(NeverDownError):
    """Base exception for security-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SECURITY_ERROR", details)


class TooManySecretsError(SecurityError):
    """Raised when too many secrets are found in a repository."""
    
    def __init__(self, secret_count: int, threshold: int):
        super().__init__(
            f"Found {secret_count} secrets, exceeds threshold of {threshold}",
            {"secret_count": secret_count, "threshold": threshold},
        )
        self.code = "TOO_MANY_SECRETS"


class SanitizationFailedError(SecurityError):
    """Raised when sanitization process fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        details = {"file_path": file_path} if file_path else {}
        super().__init__(message, details)
        self.code = "SANITIZATION_FAILED"


class UnauthorizedRepoError(SecurityError):
    """Raised when attempting to access a non-whitelisted repository."""
    
    def __init__(self, repo_url: str):
        super().__init__(
            f"Repository not in allowed list: {repo_url}",
            {"repo_url": repo_url},
        )
        self.code = "UNAUTHORIZED_REPO"


# =============================================================================
# Agent Exceptions
# =============================================================================

class AgentError(NeverDownError):
    """Base exception for agent-related errors."""
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["agent"] = agent_name
        super().__init__(message, "AGENT_ERROR", details)


class DetectiveError(AgentError):
    """Raised when the Detective agent fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "detective", details)
        self.code = "DETECTIVE_ERROR"


class ReasonerError(AgentError):
    """Raised when the Reasoner agent fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "reasoner", details)
        self.code = "REASONER_ERROR"


class LowConfidenceError(ReasonerError):
    """Raised when Reasoner confidence is below threshold."""
    
    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            f"Confidence {confidence:.2f} below threshold {threshold:.2f}",
            {"confidence": confidence, "threshold": threshold},
        )
        self.code = "LOW_CONFIDENCE"


class InvalidPatchError(ReasonerError):
    """Raised when generated patch is invalid."""
    
    def __init__(self, message: str, patch_content: Optional[str] = None):
        details = {}
        if patch_content:
            # Truncate for logging
            details["patch_preview"] = patch_content[:500]
        super().__init__(message, details)
        self.code = "INVALID_PATCH"


class SurgeonError(AgentError):
    """Raised when the Surgeon agent fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "surgeon", details)
        self.code = "SURGEON_ERROR"


class SandboxError(SurgeonError):
    """Raised when sandbox operations fail."""
    
    def __init__(self, message: str, container_id: Optional[str] = None):
        details = {"container_id": container_id} if container_id else {}
        super().__init__(message, details)
        self.code = "SANDBOX_ERROR"


class SandboxTimeoutError(SandboxError):
    """Raised when sandbox operation times out."""
    
    def __init__(self, timeout_seconds: int, container_id: Optional[str] = None):
        super().__init__(
            f"Sandbox operation timed out after {timeout_seconds}s",
            container_id,
        )
        self.code = "SANDBOX_TIMEOUT"


class TestFailedError(SurgeonError):
    """Raised when tests fail in sandbox."""
    
    def __init__(
        self,
        message: str,
        passed: int,
        failed: int,
        output: Optional[str] = None,
    ):
        details = {"passed": passed, "failed": failed}
        if output:
            details["output_preview"] = output[:1000]
        super().__init__(message, details)
        self.code = "TEST_FAILED"


class VerificationFailedError(SurgeonError):
    """Raised when patch verification fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "verifier", details)
        self.code = "VERIFICATION_FAILED"


class PRManagerError(AgentError):
    """Raised when the PR Manager agent fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "pr_manager", details)
        self.code = "PR_MANAGER_ERROR"


class GitHubAPIError(PRManagerError):
    """Raised when GitHub API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        details = {"status_code": status_code} if status_code else {}
        super().__init__(message, details)
        self.code = "GITHUB_API_ERROR"


# =============================================================================
# Orchestration Exceptions
# =============================================================================

class OrchestrationError(NeverDownError):
    """Base exception for orchestration errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ORCHESTRATION_ERROR", details)


class InvalidStateTransitionError(OrchestrationError):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(self, from_state: str, to_state: str, event: str):
        super().__init__(
            f"Invalid transition from {from_state} to {to_state} on event {event}",
            {"from_state": from_state, "to_state": to_state, "event": event},
        )
        self.code = "INVALID_STATE_TRANSITION"


class MaxRetriesExceededError(OrchestrationError):
    """Raised when maximum retry attempts are exceeded."""
    
    def __init__(self, operation: str, max_retries: int):
        super().__init__(
            f"Max retries ({max_retries}) exceeded for {operation}",
            {"operation": operation, "max_retries": max_retries},
        )
        self.code = "MAX_RETRIES_EXCEEDED"


class TimeoutError(OrchestrationError):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            f"Operation {operation} timed out after {timeout_seconds}s",
            {"operation": operation, "timeout_seconds": timeout_seconds},
        )
        self.code = "TIMEOUT"


class CircuitBreakerOpenError(OrchestrationError):
    """Raised when circuit breaker is open."""
    
    def __init__(self, service: str, failure_count: int):
        super().__init__(
            f"Circuit breaker open for {service} after {failure_count} failures",
            {"service": service, "failure_count": failure_count},
        )
        self.code = "CIRCUIT_BREAKER_OPEN"


# =============================================================================
# Data/Repository Exceptions
# =============================================================================

class DataError(NeverDownError):
    """Base exception for data access errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATA_ERROR", details)


class IncidentNotFoundError(DataError):
    """Raised when an incident is not found."""
    
    def __init__(self, incident_id: str):
        super().__init__(
            f"Incident not found: {incident_id}",
            {"incident_id": incident_id},
        )
        self.code = "INCIDENT_NOT_FOUND"


class PatchNotFoundError(DataError):
    """Raised when a patch is not found."""
    
    def __init__(self, patch_id: str):
        super().__init__(
            f"Patch not found: {patch_id}",
            {"patch_id": patch_id},
        )
        self.code = "PATCH_NOT_FOUND"


# =============================================================================
# External Service Exceptions
# =============================================================================

class ExternalServiceError(NeverDownError):
    """Base exception for external service errors."""
    
    def __init__(
        self,
        message: str,
        service: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service"] = service
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class LLMError(ExternalServiceError):
    """Raised when LLM API calls fail."""
    
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"llm_{provider}", details)
        self.code = "LLM_ERROR"


class DockerError(ExternalServiceError):
    """Raised when Docker operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "docker", details)
        self.code = "DOCKER_ERROR"
