"""Incident management endpoints."""

from enum import Enum
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import IncidentNotFoundError
from database.connection import get_db_session, get_session
from database.models import IncidentORM
from database.repositories.audit_repo import AuditRepository
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository
from models.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentDetailedResponse,
    IncidentSeverity,
    IncidentStatus,
    IncidentSummary,
)
from pydantic import BaseModel, Field
from services.orchestrator import Orchestrator, OrchestrationContext

router = APIRouter()
logger = get_logger(__name__)


async def check_sha_deduplication(
    session: AsyncSession,
    repo_url: str,
    commit_sha: Optional[str],
) -> Optional[UUID]:
    """Check if an incident for the same Commit SHA is already active."""
    if not commit_sha:
        return None
        
    stmt = select(IncidentORM.id).where(
        and_(
            IncidentORM.status.in_([IncidentStatus.PROCESSING, IncidentStatus.PENDING, IncidentStatus.AWAITING_REVIEW]),
            IncidentORM.incident_metadata["repository"]["url"].astext == repo_url,
            IncidentORM.incident_metadata["repository"]["commit"].astext == commit_sha
        )
    ).limit(1)
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def check_circuit_breaker(
    session: AsyncSession,
    repo_url: str,
    limit_count: int = 2,
    window_minutes: int = 5
) -> bool:
    """Check if the incident threshold for a repository has been exceeded."""
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    
    # Query for incidents created for this repo in the window
    stmt = select(func.count(IncidentORM.id)).where(
        and_(
            IncidentORM.created_at >= since,
            IncidentORM.incident_metadata["repository"]["url"].astext == repo_url
        )
    )
    
    result = await session.execute(stmt)
    count = result.scalar() or 0
    
    return count > limit_count


async def process_incident_async(
    incident_id: UUID,
    repo_url: str,
    logs: Optional[str] = None,
) -> None:
    """Background task to process an incident through the pipeline.
    
    If no error logs are provided, the incident enters MONITORING mode
    (Dormant Sentinel) and waits for webhook activation.
    
    Creates its own database session since background tasks run
    after the request context ends.
    """
    import traceback
    print(f"[DEBUG] process_incident_async STARTED for {incident_id}")  # Direct stdout
    logger.info("Starting incident processing", incident_id=str(incident_id))
    
    settings = get_settings()

    # SAFETY CHECK 1: Global Halt
    if settings.AGENTS_HALTED:
        logger.info("Global agents halt is active, skipping pipeline", incident_id=str(incident_id))
        async with get_session() as session:
             repo = IncidentRepository(session)
             await repo.update_status(incident_id, IncidentStatus.MONITORING)
             await repo.add_timeline_event(incident_id, "HALTED", {"reason": "Global agents halt enabled by user"})
             await session.commit()
        return

    # SAFETY CHECK 2: Circuit Breaker (2 calls per 5 mins per repo)
    async with get_session() as session:
        if await check_circuit_breaker(session, repo_url, limit_count=2, window_minutes=5):
            logger.warning("CIRCUIT BREAKER TRIGGERED for repo", repo_url=repo_url)
            repo = IncidentRepository(session)
            await repo.update_status(incident_id, IncidentStatus.FAILED)
            await repo.add_timeline_event(
                incident_id, 
                "CIRCUIT_BREAKER_TRIGGERED", 
                {"reason": "Exceeded 2 incidents per 5 minutes threshold to prevent token waste"}
            )
            await session.commit()
            return

    # Check if we have actual error logs to process
    # If not, enter MONITORING mode (Dormant Sentinel)
    has_error_logs = logs and len(logs.strip()) > 20 and "error" in logs.lower()

    if not has_error_logs:
        logger.info(
            "No error logs provided - entering MONITORING mode (Dormant Sentinel)",
            incident_id=str(incident_id),
        )
        try:
            async with get_session() as session:
                incident_repo = IncidentRepository(session)
                await incident_repo.update_status(incident_id, IncidentStatus.MONITORING)
                await incident_repo.add_timeline_event(
                    incident_id,
                    "MONITORING_STARTED",
                    {"message": "Dormant Sentinel active - watching for CI failures via webhooks"},
                )
                await session.commit()
        except Exception as e:
            logger.exception("Failed to set MONITORING status", error=str(e))
        return  # Don't run pipeline, wait for webhooks
    
    try:
        async with get_session() as session:
            # Create repositories
            incident_repo = IncidentRepository(session)
            patch_repo = PatchRepository(session)
            audit_repo = AuditRepository(session)
            
            # Create orchestrator
            orchestrator = Orchestrator(
                incident_repo=incident_repo,
                patch_repo=patch_repo,
                audit_repo=audit_repo,
            )
            
            # Build context
            context = OrchestrationContext(
                incident_id=incident_id,
                repo_url=repo_url,
                logs=logs,
            )
            
            # Run the full pipeline
            success = await orchestrator.process_incident(context)
            
            if success:
                logger.info(
                    "Incident processing completed successfully",
                    incident_id=str(incident_id),
                    pr_url=context.pull_request.pr_url if context.pull_request else None,
                )
            else:
                logger.warning(
                    "Incident processing failed",
                    incident_id=str(incident_id),
                )
    except Exception as e:
        logger.exception(
            "Fatal error in incident processing",
            incident_id=str(incident_id),
            error=str(e),
        )


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(
    data: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new incident and start processing.
    
    This endpoint accepts incident data from CI/CD webhooks, monitoring
    systems, or manual submission. The incident is queued for async
    processing through the agent pipeline.
    """
    logger.info(
        "Creating incident",
        title=data.title,
        severity=data.severity.value,
        source=data.source.value,
        repo=data.metadata.repository.url
    )
    
    # SAFETY CHECK 3: Deduplication (SHA based)
    commit_sha = data.metadata.repository.commit
    repo_url = data.metadata.repository.url
    
    existing_active_id = await check_sha_deduplication(db, repo_url, commit_sha)
    if existing_active_id:
        logger.info("De-duplicating incident - existing one found for this SHA", original_incident_id=str(existing_active_id))
        # Keep existing incident as the source of truth, return its response
        repo = IncidentRepository(db)
        existing = await repo.get_by_id(existing_active_id)
        return existing.to_response()

    repo = IncidentRepository(db)
    incident = await repo.create(data)
    
    # Add timeline event
    await repo.add_timeline_event(
        incident.id,
        "RECEIVED",
        {"source": data.source.value},
    )
    
    # Commit so incident is visible
    await db.commit()
    
    # Check if we have actual error logs to process
    # If not, enter MONITORING mode (Dormant Sentinel) immediately
    has_error_logs = data.logs and len(data.logs.strip()) > 20 and "error" in data.logs.lower()
    
    if not has_error_logs:
        # Enter MONITORING mode - no background processing needed
        logger.info(
            "No error logs provided - entering MONITORING mode (Dormant Sentinel)",
            incident_id=str(incident.id),
        )
        await repo.update_status(incident.id, IncidentStatus.MONITORING)
        await repo.add_timeline_event(
            incident.id,
            "MONITORING_STARTED",
            {"message": "Dormant Sentinel active - watching for CI failures via webhooks"},
        )
        await db.commit()
    else:
        # Has error logs - queue for async processing
        background_tasks.add_task(
            process_incident_async,
            incident.id,
            data.metadata.repository.url,
            data.logs,
        )
    
    # Reload to get updated status
    updated_incident = await repo.get_by_id(incident.id)
    
    logger.info("Incident created", incident_id=str(incident.id))
    return updated_incident.to_response()


@router.get("/incidents", response_model=List[IncidentSummary])
async def list_incidents(
    status: Optional[IncidentStatus] = Query(None, description="Filter by status"),
    severity: Optional[IncidentSeverity] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db_session),
):
    """List incidents with optional filters."""
    repo = IncidentRepository(db)
    return await repo.list_incidents(
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
    )


@router.get("/incidents/{incident_id}/details", response_model=IncidentDetailedResponse)
async def get_incident_details(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Get full incident details including AI reasoning, patches, and verification results."""
    repo = IncidentRepository(db)
    
    try:
        details = await repo.get_incident_details(incident_id)
        return details
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Get detailed incident information including timeline."""
    repo = IncidentRepository(db)
    
    try:
        incident = await repo.get_by_id(incident_id)
        return incident.to_response()
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


# --- Feedback Models ---

class FeedbackDecision(str, Enum):
    """Decision on PR review."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"


class FeedbackRequest(BaseModel):
    """Schema for submitting feedback on a PR."""
    decision: FeedbackDecision
    feedback_text: Optional[str] = Field(default=None, description="Optional feedback text for refinement")


# --- Feedback Background Task ---

async def process_refinement_async(
    incident_id: UUID,
    feedback_text: str,
) -> None:
    """Background task to re-run refinement loop with user feedback.
    
    Runs Reasoner -> Verifier -> Publisher with feedback context.
    """
    logger.info("Starting refinement processing", incident_id=str(incident_id))
    
    try:
        async with get_session() as session:
            # Create repositories
            incident_repo = IncidentRepository(session)
            patch_repo = PatchRepository(session)
            audit_repo = AuditRepository(session)
            
            # Create orchestrator
            orchestrator = Orchestrator(
                incident_repo=incident_repo,
                patch_repo=patch_repo,
                audit_repo=audit_repo,
            )
            
            # Run the refinement loop
            success = await orchestrator.run_refinement_loop(
                incident_id=incident_id,
                feedback_text=feedback_text,
            )
            
            if success:
                logger.info(
                    "Refinement processing completed successfully",
                    incident_id=str(incident_id),
                )
            else:
                logger.warning(
                    "Refinement processing failed",
                    incident_id=str(incident_id),
                )
    except Exception as e:
        logger.exception(
            "Fatal error in refinement processing",
            incident_id=str(incident_id),
            error=str(e),
        )


# --- Feedback Endpoint ---

@router.post("/incidents/{incident_id}/feedback", response_model=IncidentResponse)
async def submit_feedback(
    incident_id: UUID,
    feedback: FeedbackRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Submit feedback on a PR for human-in-the-loop review.
    
    - APPROVE: Mark incident as RESOLVED
    - REQUEST_CHANGES: Store feedback and trigger refinement loop
    """
    repo = IncidentRepository(db)
    
    try:
        incident = await repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    # Only allow feedback on PR_CREATED or AWAITING_REVIEW incidents
    if incident.status not in (IncidentStatus.PR_CREATED, IncidentStatus.AWAITING_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit feedback for incident with status {incident.status.value}. Expected PR_CREATED or AWAITING_REVIEW.",
        )
    
    if feedback.decision == FeedbackDecision.APPROVE:
        # Mark as resolved
        await repo.update_status(incident_id, IncidentStatus.RESOLVED)
        await repo.add_timeline_event(
            incident_id,
            "FEEDBACK_APPROVED",
            {"decision": "approve"},
        )
        await db.commit()
        
        logger.info("Feedback APPROVE received", incident_id=str(incident_id))
        
    elif feedback.decision == FeedbackDecision.REQUEST_CHANGES:
        # Check iteration limit (max 3 refinements)
        max_iterations = 3
        if incident.feedback_iteration >= max_iterations:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum refinement iterations ({max_iterations}) reached",
            )
        
        # Store feedback and update status
        feedback_text = feedback.feedback_text or "User requested changes"
        await repo.set_feedback(incident_id, feedback_text)
        await repo.update_status(incident_id, IncidentStatus.PROCESSING)
        await repo.add_timeline_event(
            incident_id,
            "FEEDBACK_REQUEST_CHANGES",
            {
                "decision": "request_changes",
                "feedback": feedback_text,
                "iteration": incident.feedback_iteration + 1,
            },
        )
        await db.commit()
        
        logger.info(
            "Feedback REQUEST_CHANGES received, triggering refinement",
            incident_id=str(incident_id),
            iteration=incident.feedback_iteration + 1,
        )
        
        # Queue refinement processing
        background_tasks.add_task(
            process_refinement_async,
            incident_id,
            feedback_text,
        )
    
    # Return updated incident
    incident = await repo.get_by_id(incident_id)
    return incident.to_response()


@router.post("/incidents/{incident_id}/retry", response_model=IncidentResponse)
async def retry_incident(
    incident_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Retry processing a failed incident."""
    repo = IncidentRepository(db)
    
    try:
        incident = await repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    if incident.status not in (
        IncidentStatus.FAILED, IncidentStatus.COMPLETED, 
        IncidentStatus.PROCESSING, IncidentStatus.PENDING,
        IncidentStatus.MONITORING,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry incident with status {incident.status.value}",
        )
    
    # Update status to pending
    await repo.update_status(incident_id, IncidentStatus.PENDING)
    await repo.add_timeline_event(
        incident_id,
        "RETRY_REQUESTED",
        {"previous_status": incident.status.value},
    )
    await db.commit()
    
    # Extract repo_url and logs from incident (Pydantic Incident model)
    repo_url = incident.metadata.repository.url if incident.metadata else ""
    logs = incident.logs
    
    # On retry, ensure we have logs so process_incident_async runs the full
    # pipeline instead of entering MONITORING mode. The original webhook
    # activation already proved CI errors existed.
    if not logs or len(logs.strip()) < 20 or "error" not in logs.lower():
        logs = f"[RETRY] Previously detected CI error for {repo_url}. Re-running full pipeline."
    
    # Queue for processing
    background_tasks.add_task(process_incident_async, incident_id, repo_url, logs)
    
    incident = await repo.get_by_id(incident_id)
    return incident.to_response()


@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an incident (admin only in production)."""
    # TODO: Add admin authentication check
    
    repo = IncidentRepository(db)
    
    try:
        await repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    # Delete via ORM
    from database.models import IncidentORM
    from sqlalchemy import delete
    
    stmt = delete(IncidentORM).where(IncidentORM.id == incident_id)
    await db.execute(stmt)
    await db.commit()
    
    logger.info("Incident deleted", incident_id=str(incident_id))
