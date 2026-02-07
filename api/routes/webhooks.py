"""Webhook endpoints for external integrations."""

import hashlib
import hmac
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from config.settings import get_settings
from database.connection import get_db_session
from database.repositories.incident_repo import IncidentRepository
from models.incident import (
    IncidentCreate,
    IncidentMetadata,
    IncidentSeverity,
    IncidentSource,
    RepositoryInfo,
)

router = APIRouter()
logger = get_logger(__name__)


def verify_github_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify GitHub webhook signature (HMAC-SHA256)."""
    if not signature.startswith("sha256="):
        return False
    
    expected_sig = signature[7:]  # Remove "sha256=" prefix
    computed_sig = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(expected_sig, computed_sig)


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Handle GitHub webhooks for CI failures and other events.
    
    Supported events:
    - workflow_run: When a GitHub Actions workflow completes
    - check_run: When a check run completes
    """
    settings = get_settings()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature if secret is configured
    if settings.GITHUB_WEBHOOK_SECRET:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        if not verify_github_signature(
            body,
            x_hub_signature_256,
            settings.GITHUB_WEBHOOK_SECRET.get_secret_value(),
        ):
            logger.warning("Invalid GitHub webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info(
        "Received GitHub webhook",
        event=x_github_event,
        action=payload.get("action"),
    )
    
    # Handle workflow_run events (GitHub Actions)
    if x_github_event == "workflow_run":
        return await handle_workflow_run(payload, background_tasks, db)
    
    # Handle check_run events
    if x_github_event == "check_run":
        return await handle_check_run(payload, background_tasks, db)
    
    # Acknowledge but don't process other events
    return {"status": "ignored", "event": x_github_event}


async def handle_workflow_run(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Handle workflow_run webhook event."""
    workflow_run = payload.get("workflow_run", {})
    action = payload.get("action")
    
    # Only process completed, failed runs
    if action != "completed" or workflow_run.get("conclusion") != "failure":
        return {"status": "ignored", "reason": "not a failure"}
    
    repo = payload.get("repository", {})
    
    # Create incident
    incident_data = IncidentCreate(
        title=f"CI Failure: {workflow_run.get('name', 'Unknown workflow')}",
        description=f"GitHub Actions workflow failed on branch {workflow_run.get('head_branch')}",
        severity=IncidentSeverity.HIGH,
        source=IncidentSource.CI,
        metadata=IncidentMetadata(
            repository=RepositoryInfo(
                url=repo.get("html_url", ""),
                branch=workflow_run.get("head_branch", "main"),
                commit=workflow_run.get("head_sha"),
            ),
            workflow_name=workflow_run.get("name"),
            job_url=workflow_run.get("html_url"),
        ),
    )
    
    incident_repo = IncidentRepository(db)
    incident = await incident_repo.create(incident_data)
    
    logger.info(
        "Created incident from workflow_run webhook",
        incident_id=str(incident.id),
        workflow=workflow_run.get("name"),
    )
    
    # Queue for processing
    from api.routes.incidents import process_incident_async
    background_tasks.add_task(process_incident_async, incident.id)
    
    return {
        "status": "created",
        "incident_id": str(incident.id),
    }


async def handle_check_run(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Handle check_run webhook event."""
    check_run = payload.get("check_run", {})
    action = payload.get("action")
    
    # Only process completed, failed checks
    if action != "completed" or check_run.get("conclusion") != "failure":
        return {"status": "ignored", "reason": "not a failure"}
    
    repo = payload.get("repository", {})
    
    # Create incident
    incident_data = IncidentCreate(
        title=f"Check Failed: {check_run.get('name', 'Unknown check')}",
        description=check_run.get("output", {}).get("summary", "Check run failed"),
        severity=IncidentSeverity.MEDIUM,
        source=IncidentSource.CI,
        logs=check_run.get("output", {}).get("text", ""),
        metadata=IncidentMetadata(
            repository=RepositoryInfo(
                url=repo.get("html_url", ""),
                branch=check_run.get("check_suite", {}).get("head_branch", "main"),
                commit=check_run.get("head_sha"),
            ),
            job_url=check_run.get("html_url"),
        ),
    )
    
    incident_repo = IncidentRepository(db)
    incident = await incident_repo.create(incident_data)
    
    logger.info(
        "Created incident from check_run webhook",
        incident_id=str(incident.id),
        check_name=check_run.get("name"),
    )
    
    # Queue for processing
    from api.routes.incidents import process_incident_async
    background_tasks.add_task(process_incident_async, incident.id)
    
    return {
        "status": "created",
        "incident_id": str(incident.id),
    }


@router.post("/webhooks/datadog")
async def datadog_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Handle Datadog alert webhooks."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    logger.info("Received Datadog webhook", alert_type=payload.get("alert_type"))
    
    # Parse Datadog alert format
    event_type = payload.get("event_type", "")
    
    # Only process alerts (not recoveries)
    if "alert" not in event_type.lower():
        return {"status": "ignored", "reason": "not an alert"}
    
    # Datadog doesn't always include repo info, so this may need customization
    # based on how alerts are configured
    incident_data = IncidentCreate(
        title=payload.get("title", "Datadog Alert"),
        description=payload.get("body", ""),
        severity=IncidentSeverity.HIGH if payload.get("priority") == "P1" else IncidentSeverity.MEDIUM,
        source=IncidentSource.MONITORING,
        logs=payload.get("event_msg", ""),
        metadata=IncidentMetadata(
            repository=RepositoryInfo(
                url=payload.get("tags", {}).get("repository", ""),
                branch=payload.get("tags", {}).get("branch", "main"),
            ),
            alert_id=payload.get("id"),
            tags=payload.get("tags", []) if isinstance(payload.get("tags"), list) else [],
        ),
    )
    
    incident_repo = IncidentRepository(db)
    incident = await incident_repo.create(incident_data)
    
    logger.info(
        "Created incident from Datadog webhook",
        incident_id=str(incident.id),
    )
    
    # Queue for processing
    from api.routes.incidents import process_incident_async
    background_tasks.add_task(process_incident_async, incident.id)
    
    return {
        "status": "created",
        "incident_id": str(incident.id),
    }
