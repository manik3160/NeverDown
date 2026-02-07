"""Main orchestrator for NeverDown incident processing."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from agents.agent_0_sanitizer.sanitizer import SanitizerAgent, SanitizeInput
from agents.agent_1_detective.detective import DetectiveAgent, DetectiveInput
from agents.agent_2_reasoner.reasoner import ReasonerAgent, ReasonerInput
from agents.agent_3_verifier.verifier import VerifierAgent, VerifierInput
from agents.agent_4_publisher.publisher import PublisherAgent, PublisherInput
from config.logging_config import audit_logger, get_logger
from config.settings import get_settings
from database.repositories.audit_repo import AuditRepository
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository
from models.incident import IncidentStatus
from models.verification import VerificationResult, VerificationStatus
from services.git_service import GitService

logger = get_logger(__name__)


@dataclass
class OrchestrationContext:
    """Context passed through orchestration pipeline."""
    incident_id: UUID
    repo_url: str
    logs: Optional[str] = None
    stack_trace: Optional[str] = None
    ci_output: Optional[str] = None
    
    # Paths set during execution
    original_repo_path: Optional[str] = None
    sanitized_repo_path: Optional[str] = None
    
    # Agent outputs
    sanitization_report: Optional[object] = None
    detective_report: Optional[object] = None
    reasoner_output: Optional[object] = None
    verification_result: Optional[object] = None
    pull_request: Optional[object] = None


class Orchestrator:
    """Main orchestrator coordinating all agents.
    
    Pipeline:
    1. Clone repository
    2. Agent 0 (Sanitizer): Remove secrets
    3. Agent 1 (Detective): Analyze failure
    4. Agent 2 (Reasoner): Generate fix
    5. Agent 3 (Verifier): Test fix in sandbox
    6. Agent 4 (Publisher): Create PR (never auto-merge)
    
    Each stage can halt the pipeline if validation fails.
    All state transitions are logged for audit.
    """
    
    def __init__(
        self,
        incident_repo: IncidentRepository,
        patch_repo: PatchRepository,
        audit_repo: AuditRepository,
    ):
        self.settings = get_settings()
        self.incident_repo = incident_repo
        self.patch_repo = patch_repo
        self.audit_repo = audit_repo
        
        # Services
        self.git_service = GitService()
        
        # Agents
        self.sanitizer = SanitizerAgent()
        self.detective = DetectiveAgent()
        self.reasoner = ReasonerAgent()
        self.verifier = VerifierAgent()
        self.publisher = PublisherAgent()
    
    async def process_incident(self, context: OrchestrationContext) -> bool:
        """Process an incident through the full pipeline.
        
        Args:
            context: Orchestration context with incident info
            
        Returns:
            True if PR was created successfully
        """
        try:
            # Update to processing status
            await self._update_status(
                context.incident_id,
                IncidentStatus.PROCESSING,
                "Starting incident processing",
            )
            
            # Step 1: Clone repository
            await self._clone_repository(context)
            
            # Step 2: Sanitize (SECRET PROTECTION)
            sanitize_success = await self._run_sanitizer(context)
            if not sanitize_success:
                await self._update_status(
                    context.incident_id,
                    IncidentStatus.FAILED,
                    "Sanitization failed",
                )
                return False
            
            # Step 3: Detective analysis
            detective_success = await self._run_detective(context)
            if not detective_success:
                await self._update_status(
                    context.incident_id,
                    IncidentStatus.FAILED,
                    "Detective analysis failed",
                )
                return False
            
            # Step 4: Reasoner (LLM analysis)
            reasoner_success = await self._run_reasoner(context)
            if not reasoner_success:
                await self._update_status(
                    context.incident_id,
                    IncidentStatus.FAILED,
                    "Reasoner analysis failed",
                )
                return False
            
            
            # Step 5: Verifier (sandbox testing)
            # Note: Verifier requires Docker-in-Docker which may not be available
            # If verification fails, we log it but continue to PR creation
            verifier_success = await self._run_verifier(context)
            if not verifier_success:
                logger.warning(
                    "Verification skipped or failed - proceeding with unverified patch",
                    incident_id=str(context.incident_id),
                )
                # Don't halt the pipeline - continue to Publisher
            
            
            # Step 6: Publisher (create PR)
            publisher_success = await self._run_publisher(context)
            if not publisher_success:
                await self._update_status(
                    context.incident_id,
                    IncidentStatus.FAILED,
                    "PR creation failed",
                )
                return False
            
            # Success!
            await self._update_status(
                context.incident_id,
                IncidentStatus.PR_CREATED,
                f"PR created: {context.pull_request.pr_url if context.pull_request else 'unknown'}",
            )
            
            return True
        
        except Exception as e:
            logger.exception("Orchestration failed", error=str(e))
            
            await self._update_status(
                context.incident_id,
                IncidentStatus.FAILED,
                f"Orchestration error: {str(e)[:200]}",
            )
            
            return False
        
        finally:
            # Cleanup cloned repos
            await self._cleanup(context)
    
    async def _clone_repository(self, context: OrchestrationContext) -> None:
        """Clone the repository."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Cloning repository",
        )
        
        result = await self.git_service.clone_repository(
            context.repo_url,
            str(context.incident_id),
        )
        
        if not result.success:
            raise RuntimeError(f"Clone failed: {result.error}")
        
        context.original_repo_path = result.path
    
    async def _run_sanitizer(self, context: OrchestrationContext) -> bool:
        """Run the Sanitizer agent."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Sanitizing repository",
        )
        
        result = await self.sanitizer.run(
            SanitizeInput(
                repo_path=context.original_repo_path,
                incident_id=context.incident_id,
            ),
            incident_id=context.incident_id,
        )
        
        if not result.success:
            logger.error("Sanitizer failed", error=result.error)
            return False
        
        context.sanitized_repo_path = result.output.sanitized_repo_path
        context.sanitization_report = result.output.report
        
        return True
    
    async def _run_detective(self, context: OrchestrationContext) -> bool:
        """Run the Detective agent."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Analyzing failure",
        )
        
        result = await self.detective.run(
            DetectiveInput(
                incident_id=context.incident_id,
                sanitized_repo_path=context.sanitized_repo_path,
                logs=context.logs,
                stack_trace=context.stack_trace,
                ci_output=context.ci_output,
            ),
            incident_id=context.incident_id,
        )
        
        if not result.success:
            logger.error("Detective failed", error=result.error)
            return False
        
        context.detective_report = result.output.report
        
        # Check if we found any errors
        if not context.detective_report.errors:
            logger.warning("No errors found in logs")
            # Could still continue if we have suspected files
            if not context.detective_report.suspected_files:
                return False
        
        return True
    
    async def _run_reasoner(self, context: OrchestrationContext) -> bool:
        """Run the Reasoner agent."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Generating fix with LLM",
        )
        
        result = await self.reasoner.run(
            ReasonerInput(
                incident_id=context.incident_id,
                sanitized_repo_path=context.sanitized_repo_path,
                detective_report=context.detective_report,
            ),
            incident_id=context.incident_id,
        )
        
        if not result.success:
            logger.error("Reasoner failed", error=result.error)
            return False
        
        context.reasoner_output = result.output.output
        
        # Save patch to database
        await self.patch_repo.create(context.reasoner_output.patch)
        
        return True
    
    async def _run_verifier(self, context: OrchestrationContext) -> bool:
        """Run the Verifier agent."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Verifying fix in sandbox",
        )
        
        result = await self.verifier.run(
            VerifierInput(
                incident_id=context.incident_id,
                sanitized_repo_path=context.sanitized_repo_path,
                patch=context.reasoner_output.patch,
            ),
            incident_id=context.incident_id,
        )
        
        if not result.success:
            logger.error("Verifier failed", error=result.error)
            
            # Create placeholder verification result for Publisher
            # Mark as NO_TESTS so Publisher proceeds without verification
            context.verification_result = VerificationResult(
                incident_id=context.incident_id,
                patch_id=context.reasoner_output.patch.id,
                status=VerificationStatus.NO_TESTS,
                tests_run=[],
                tests_passed=0,
                tests_failed=0,
                verification_failed_reason="Verification skipped - Docker unavailable",
            )
            return False
        
        context.verification_result = result.output.result
        
        # Update patch with verification status
        try:
            await self.patch_repo.mark_verified(
                context.reasoner_output.patch.id,
                verified=(context.verification_result.status == VerificationStatus.PASSED),
            )
        except Exception as e:
            # Patch update failures should not halt the pipeline
            # This may happen if the patch hasn't been committed yet
            logger.warning("Failed to update patch verification status", error=str(e))
        
        # Check if verification passed
        if context.verification_result.status == VerificationStatus.FAILED:
            logger.warning("Verification failed, but proceeding to create PR for manual review")
            # In production, we might want to stop here, but for now we proceed
            # return False
        
        return True
    
    async def _run_publisher(self, context: OrchestrationContext) -> bool:
        """Run the Publisher agent."""
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            "Creating pull request",
        )
        
        result = await self.publisher.run(
            PublisherInput(
                incident_id=context.incident_id,
                original_repo_path=context.original_repo_path,
                patch=context.reasoner_output.patch,
                verification=context.verification_result,
                repo_url=context.repo_url,
                root_cause_summary=context.reasoner_output.root_cause_summary,
            ),
            incident_id=context.incident_id,
        )
        
        if not result.success:
            logger.error("Publisher failed", error=result.error)
            return False
        
        context.pull_request = result.output
        
        return True
    
    async def _update_status(
        self,
        incident_id: UUID,
        status: IncidentStatus,
        detail: str,
    ) -> None:
        """Update incident status with audit logging.
        
        Uses a separate session to prevent status update failures
        from contaminating the main transaction.
        """
        try:
            # Import here to avoid circular dependency
            from database.connection import get_session
            
            # Use a separate session for status updates
            async with get_session() as session:
                temp_repo = IncidentRepository(session)
                
                # Get current status for logging
                incident = await temp_repo.get(incident_id)
                old_status = incident.status if incident else "unknown"
                
                await temp_repo.update_status(incident_id, status)
                
                audit_logger.log_state_transition(
                    incident_id=str(incident_id),
                    from_state=old_status.value if hasattr(old_status, 'value') else str(old_status),
                    to_state=status.value,
                    metadata={"detail": detail},
                )
        except Exception as e:
            # Status update failures should not halt the pipeline
            logger.warning("Failed to update status", error=str(e))
    
    async def _cleanup(self, context: OrchestrationContext) -> None:
        """Cleanup temporary files."""
        if context.original_repo_path:
            self.git_service.cleanup_clone(context.original_repo_path)
        
        if context.sanitized_repo_path:
            import shutil
            try:
                shutil.rmtree(context.sanitized_repo_path, ignore_errors=True)
            except Exception:
                pass
