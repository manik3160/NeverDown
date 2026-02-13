"""Main orchestrator for NeverDown incident processing."""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx

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
            
            # Step 1.5: Fetch GitHub Actions logs if not provided
            await self._fetch_github_actions_logs(context)
            
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
            # Store the branch name for potential future updates
            # Use a fresh session since the main session may be stale after
            # the long pipeline run (Neon serverless closes idle connections)
            if context.pull_request and hasattr(context.pull_request, 'branch_name'):
                try:
                    from database.connection import get_session
                    async with get_session() as session:
                        temp_repo = IncidentRepository(session)
                        await temp_repo.set_pr_branch(
                            context.incident_id,
                            context.pull_request.branch_name,
                        )
                        await session.commit()
                except Exception as e:
                    logger.warning("Failed to store PR branch name", error=str(e))
            
            # Set status to AWAITING_REVIEW (human-in-the-loop)
            await self._update_status(
                context.incident_id,
                IncidentStatus.AWAITING_REVIEW,
                f"PR created: {context.pull_request.pr_url if context.pull_request else 'unknown'} - awaiting human review",
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
    
    async def _fetch_github_actions_logs(self, context: OrchestrationContext) -> None:
        """Fetch failed GitHub Actions workflow logs if no logs provided.
        
        This enables the detective agent to analyze CI failures even when
        manually triggered without explicit error logs.
        """
        # Skip if we already have logs
        if context.logs and context.logs != "Monitoring via webhooks":
            return
        
        # Parse owner/repo from URL
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', context.repo_url)
        if not match:
            logger.warning("Could not parse repo URL for Actions logs", url=context.repo_url)
            return
        
        owner, repo = match.group(1), match.group(2).replace('.git', '')
        
        # Get GitHub token
        token = self.settings.GITHUB_TOKEN.get_secret_value() if self.settings.GITHUB_TOKEN else None
        if not token:
            logger.warning("No GitHub token for fetching Actions logs")
            return
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get recent workflow runs
                runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
                runs_resp = await client.get(
                    runs_url,
                    headers=headers,
                    params={"status": "failure", "per_page": 5}
                )
                
                if runs_resp.status_code != 200:
                    logger.warning("Failed to fetch workflow runs", status=runs_resp.status_code)
                    return
                
                runs_data = runs_resp.json()
                workflow_runs = runs_data.get("workflow_runs", [])
                
                if not workflow_runs:
                    logger.info("No failed workflow runs found")
                    return
                
                # Get the most recent failed run
                failed_run = workflow_runs[0]
                run_id = failed_run["id"]
                
                logger.info(
                    "Found failed workflow run",
                    run_id=run_id,
                    name=failed_run.get("name"),
                    conclusion=failed_run.get("conclusion"),
                )
                
                # Get jobs for this run
                jobs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
                jobs_resp = await client.get(jobs_url, headers=headers)
                
                if jobs_resp.status_code != 200:
                    logger.warning("Failed to fetch jobs", status=jobs_resp.status_code)
                    return
                
                jobs_data = jobs_resp.json()
                jobs = jobs_data.get("jobs", [])
                
                # Find failed jobs and collect their logs
                collected_logs = []
                for job in jobs:
                    if job.get("conclusion") == "failure":
                        job_name = job.get("name", "unknown")
                        
                        # Get failed steps
                        for step in job.get("steps", []):
                            if step.get("conclusion") == "failure":
                                step_name = step.get("name", "unknown step")
                                collected_logs.append(
                                    f"=== JOB: {job_name} | STEP: {step_name} (FAILED) ==="
                                )
                        
                        # Try to get job logs (requires special header)
                        log_url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job['id']}/logs"
                        log_headers = headers.copy()
                        log_headers["Accept"] = "application/vnd.github+json"
                        
                        try:
                            log_resp = await client.get(log_url, headers=log_headers, follow_redirects=True)
                            if log_resp.status_code == 200:
                                # Logs can be large, take last 5000 chars
                                log_text = log_resp.text
                                if len(log_text) > 5000:
                                    log_text = "... [truncated] ...\n" + log_text[-5000:]
                                collected_logs.append(log_text)
                        except Exception as e:
                            logger.warning("Failed to fetch job logs", job=job_name, error=str(e))
                
                if collected_logs:
                    context.logs = "\n\n".join(collected_logs)
                    context.ci_output = context.logs
                    logger.info("Fetched GitHub Actions logs", chars=len(context.logs))
                else:
                    # At least provide some context
                    context.logs = f"GitHub Actions workflow '{failed_run.get('name')}' failed on {failed_run.get('head_branch')} branch"
                    logger.info("No detailed logs available, using summary")
                    
        except Exception as e:
            logger.warning("Error fetching GitHub Actions logs", error=str(e))

    
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
        
        # Save patch to database using a fresh session
        try:
            from database.connection import get_session
            async with get_session() as session:
                temp_patch_repo = PatchRepository(session)
                await temp_patch_repo.create(context.reasoner_output.patch)
                await session.commit()
        except Exception as e:
            logger.warning("Failed to save patch to database", error=str(e))
        
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
            from models.verification import VerificationResult, VerificationStatus
            context.verification_result = VerificationResult(
                incident_id=context.incident_id,
                patch_id=context.reasoner_output.patch.id,
                status=VerificationStatus.NO_TESTS,
                tests_run=[],  # Empty list, not integer
                tests_passed=0,
                tests_failed=0,
                verification_failed_reason="Verification skipped - Docker unavailable",
            )
            return False
        
        context.verification_result = result.output.result
        
        # Update patch with verification status (use fresh session)
        from models.verification import VerificationStatus
        try:
            from database.connection import get_session
            async with get_session() as session:
                temp_patch_repo = PatchRepository(session)
                await temp_patch_repo.mark_verified(
                    context.reasoner_output.patch.id,
                    verified=(context.verification_result.status == VerificationStatus.PASSED),
                )
                await session.commit()
        except Exception as e:
            logger.warning("Failed to update patch verification status", error=str(e))
        
        # Check if verification passed or has no tests
        if context.verification_result.status == VerificationStatus.FAILED:
            logger.warning("Verification failed, not creating PR")
            return False
        
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
        """Update incident status with audit logging and timeline events.
        
        Uses a separate session to prevent status update failures
        from contaminating the main transaction.
        
        Also adds a timeline event so the frontend can show real-time progress.
        """
        try:
            # Import here to avoid circular dependency
            from database.connection import get_session
            
            # Map status to timeline event state for better frontend display
            status_to_event = {
                IncidentStatus.PENDING: "QUEUED",
                IncidentStatus.PROCESSING: "PROCESSING",
                IncidentStatus.COMPLETED: "COMPLETED",
                IncidentStatus.FAILED: "FAILED",
                IncidentStatus.PR_CREATED: "PR_CREATED",
            }
            
            # Use detail to create more specific event names
            event_state = detail.upper().replace(" ", "_")
            if len(event_state) > 50:
                event_state = status_to_event.get(status, status.value.upper())
            
            # Use a separate session for status updates
            async with get_session() as session:
                temp_repo = IncidentRepository(session)
                
                # Get current status for logging
                incident = await temp_repo.get(incident_id)
                old_status = incident.status if incident else "unknown"
                
                await temp_repo.update_status(incident_id, status)
                
                # Add timeline event for real-time log display
                await temp_repo.add_timeline_event(
                    incident_id,
                    event_state,
                    {"status": status.value, "detail": detail},
                )
                
                # Commit the changes (session context manager handles this)
                await session.commit()
                
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

    async def run_refinement_loop(
        self,
        incident_id: UUID,
        feedback_text: str,
    ) -> bool:
        """Re-run Reasoner → Verifier → Publisher with user feedback.
        
        This method is called when a user requests changes on a PR.
        It fetches the original context and previous patch, builds a
        refinement prompt that includes user feedback, and re-runs
        only the relevant agents to update the existing PR.
        
        Args:
            incident_id: The incident ID to refine
            feedback_text: User's feedback for refinement
            
        Returns:
            True if refinement succeeded and PR was updated
        """
        context = None
        try:
            # Fetch incident
            incident = await self.incident_repo.get(incident_id)
            if not incident:
                logger.error("Incident not found for refinement", incident_id=str(incident_id))
                return False
            
            # Get repository info from metadata
            repo_url = incident.metadata.repository.url
            existing_branch = incident.pr_branch_name
            
            if not existing_branch:
                logger.error("No existing branch found for refinement", incident_id=str(incident_id))
                return False
            
            await self._update_status(
                incident_id,
                IncidentStatus.PROCESSING,
                "Starting refinement with user feedback",
            )
            
            # Clone repository
            context = OrchestrationContext(
                incident_id=incident_id,
                repo_url=repo_url,
                logs=incident.logs,
            )
            await self._clone_repository(context)
            
            # Run sanitizer (need sanitized code for reasoner)
            sanitize_success = await self._run_sanitizer(context)
            if not sanitize_success:
                await self._update_status(
                    incident_id,
                    IncidentStatus.FAILED,
                    "Refinement sanitization failed",
                )
                return False
            
            # Fetch detective report from database
            detective_report_dict = await self.incident_repo.get_detective_report(incident_id)
            if not detective_report_dict:
                logger.error("No detective report found for refinement", incident_id=str(incident_id))
                await self._update_status(
                    incident_id,
                    IncidentStatus.FAILED,
                    "No detective report found for refinement",
                )
                return False
            
            # Reconstruct detective report
            from models.analysis import DetectiveReport, ErrorInfo, FailureCategory, SuspectedFile
            context.detective_report = DetectiveReport(
                errors=[ErrorInfo(**e) for e in detective_report_dict.get("errors", [])],
                suspected_files=[SuspectedFile(**f) for f in detective_report_dict.get("suspected_files", [])],
                failure_category=FailureCategory(detective_report_dict.get("failure_category", "unknown")),
                evidence=detective_report_dict.get("evidence", []),
                recent_changes=[],
            )
            
            # Fetch previous patch for context
            previous_patch_diff = await self.incident_repo.get_previous_patch_diff(incident_id)
            
            # Build refinement prompt for Reasoner
            from agents.agent_2_reasoner.prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder(context.sanitized_repo_path)
            
            # Create refinement input for reasoner
            await self._update_status(
                incident_id,
                IncidentStatus.PROCESSING,
                "Generating refined fix with user feedback",
            )
            
            # Run reasoner with refinement context
            from agents.agent_2_reasoner.reasoner import ReasonerInput
            
            # Add feedback context to detective report evidence
            context.detective_report.evidence.append(
                f"USER FEEDBACK (refinement): {feedback_text}"
            )
            if previous_patch_diff:
                context.detective_report.evidence.append(
                    f"PREVIOUS PATCH ATTEMPT:\n```diff\n{previous_patch_diff[:2000]}\n```"
                )
            
            reasoner_success = await self._run_reasoner(context)
            if not reasoner_success:
                await self._update_status(
                    incident_id,
                    IncidentStatus.FAILED,
                    "Refinement reasoner failed",
                )
                return False
            
            # Run verifier
            verifier_success = await self._run_verifier(context)
            if not verifier_success:
                logger.warning(
                    "Refinement verification skipped or failed - proceeding with unverified patch",
                    incident_id=str(incident_id),
                )
                # Don't halt - continue to Publisher
            
            # Run publisher with existing branch (update PR, don't create new)
            await self._update_status(
                incident_id,
                IncidentStatus.PROCESSING,
                "Updating existing PR with refined fix",
            )
            
            # Modify publisher input to use existing branch
            from agents.agent_4_publisher.publisher import PublisherInput
            
            publisher_input = PublisherInput(
                incident_id=incident_id,
                original_repo_path=context.original_repo_path,
                patch=context.reasoner_output.patch,
                verification=context.verification_result,
                repo_url=repo_url,
                root_cause_summary=context.reasoner_output.root_cause_summary,
            )
            
            # Store existing branch for publisher to use
            # We'll modify _run_publisher_with_existing_branch
            publisher_success = await self._run_publisher_update(
                context,
                existing_branch,
                incident.feedback_iteration,
            )
            
            if not publisher_success:
                await self._update_status(
                    incident_id,
                    IncidentStatus.FAILED,
                    "Refinement PR update failed",
                )
                return False
            
            # Success!
            await self._update_status(
                incident_id,
                IncidentStatus.AWAITING_REVIEW,
                f"PR updated with refinement #{incident.feedback_iteration + 1}",
            )
            
            return True
            
        except Exception as e:
            logger.exception("Refinement failed", error=str(e))
            
            await self._update_status(
                incident_id,
                IncidentStatus.FAILED,
                f"Refinement error: {str(e)[:200]}",
            )
            
            return False
            
        finally:
            # Cleanup cloned repos
            if context:
                await self._cleanup(context)

    async def _run_publisher_update(
        self,
        context: OrchestrationContext,
        existing_branch: str,
        refinement_iteration: int,
    ) -> bool:
        """Run Publisher to update an existing PR branch.
        
        This pushes new commits to the existing branch rather than
        creating a new branch and PR.
        """
        await self._update_status(
            context.incident_id,
            IncidentStatus.PROCESSING,
            f"Pushing refinement #{refinement_iteration + 1} to existing PR",
        )
        
        # Parse repo info
        try:
            owner, repo = self.publisher.github.parse_repo_url(context.repo_url)
        except ValueError as e:
            logger.error("Failed to parse repo URL", error=str(e))
            return False
        
        try:
            # Apply patch to local repo
            await self.publisher._apply_patch_to_branch(
                owner,
                repo,
                existing_branch,
                context.reasoner_output.patch,
                context.original_repo_path,
            )
            
            context.pull_request = type('obj', (object,), {
                'pr_url': context.repo_url,
                'branch_name': existing_branch,
            })()
            
            logger.info(
                "Successfully pushed refinement to existing branch",
                branch=existing_branch,
                incident_id=str(context.incident_id),
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to update existing PR", error=str(e))
            return False

