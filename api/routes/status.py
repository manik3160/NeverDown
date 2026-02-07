"""Incident status endpoints."""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import IncidentNotFoundError
from database.connection import get_db_session
from database.repositories.audit_repo import AuditRepository
from database.repositories.incident_repo import IncidentRepository
from database.repositories.patch_repo import PatchRepository

router = APIRouter()


@router.get("/incidents/{incident_id}/status")
async def get_incident_status(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Get detailed status of an incident including agent progress."""
    incident_repo = IncidentRepository(db)
    
    try:
        incident = await incident_repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    # Get patches for this incident
    patch_repo = PatchRepository(db)
    patches = await patch_repo.get_by_incident_id(incident_id)
    
    return {
        "incident_id": str(incident.id),
        "status": incident.status.value,
        "current_state": incident.current_state,
        "timeline": [
            {
                "state": e.state,
                "timestamp": e.timestamp.isoformat(),
                "details": e.details,
            }
            for e in incident.timeline
        ],
        "patches_generated": len(patches),
        "latest_patch_verified": patches[0].verified if patches else None,
        "pr_url": incident.pr_url,
        "error_message": incident.error_message,
    }


@router.get("/incidents/{incident_id}/audit")
async def get_incident_audit_log(
    incident_id: UUID,
    limit: int = 50,
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Get audit log for an incident."""
    incident_repo = IncidentRepository(db)
    
    try:
        await incident_repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    audit_repo = AuditRepository(db)
    return await audit_repo.get_by_incident(incident_id, limit=limit)


@router.get("/incidents/{incident_id}/patches")
async def get_incident_patches(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """Get all patches generated for an incident."""
    incident_repo = IncidentRepository(db)
    
    try:
        await incident_repo.get_by_id(incident_id)
    except IncidentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    patch_repo = PatchRepository(db)
    patches = await patch_repo.get_by_incident_id(incident_id)
    
    return [
        {
            "id": str(p.id),
            "confidence": p.confidence,
            "verified": p.verified,
            "summary": p.summary,
            "retry_count": p.retry_count,
            "created_at": p.created_at.isoformat(),
        }
        for p in patches
    ]
