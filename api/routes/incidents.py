"""Incident management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from core.exceptions import IncidentNotFoundError
from database.connection import get_db_session, get_session
from database.repositories.audit_repo import AuditRepository
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository
from models.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentSeverity,
    IncidentStatus,
    IncidentSummary,
)
from services.orchestrator import Orchestrator, OrchestrationContext

router = APIRouter()
logger = get_logger(__name__)


async def process_incident_async(
    incident_id: UUID,
    repo_url: str,
    logs: Optional[str] = None,
) -> None:
    """Background task to process an incident through the pipeline.
    
    Creates its own database session since background tasks run
    after the request context ends.
    """
    logger.info("Starting incident processing", incident_id=str(incident_id))
    
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
                    pr_url=context.pull_request.url if context.pull_request else None,
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
    )
    
    repo = IncidentRepository(db)
    incident = await repo.create(data)
    
    # Add timeline event
    await repo.add_timeline_event(
        incident.id,
        "RECEIVED",
        {"source": data.source.value},
    )
    
    # Commit so background task can see the incident
    await db.commit()
    
    # Queue for async processing with necessary context
    background_tasks.add_task(
        process_incident_async,
        incident.id,
        data.metadata.repository.url,
        data.logs,
    )
    
    logger.info("Incident created", incident_id=str(incident.id))
    return incident.to_response()


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
    
    if incident.status not in (IncidentStatus.FAILED, IncidentStatus.COMPLETED):
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
    
    # Queue for processing
    background_tasks.add_task(process_incident_async, incident_id)
    
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
