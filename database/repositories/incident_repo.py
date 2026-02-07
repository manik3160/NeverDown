"""Incident repository for data access."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import IncidentNotFoundError
from database.models import IncidentORM
from models.incident import (
    Incident,
    IncidentCreate,
    IncidentMetadata,
    IncidentResponse,
    IncidentSeverity,
    IncidentStatus,
    IncidentSummary,
    IncidentUpdate,
    RepositoryInfo,
    TimelineEvent,
)


class IncidentRepository:
    """Repository for incident data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: IncidentCreate) -> Incident:
        """Create a new incident."""
        incident_orm = IncidentORM(
            title=data.title,
            description=data.description,
            severity=data.severity,
            source=data.source,
            status=IncidentStatus.PENDING,
            logs=data.logs,
            incident_metadata=data.metadata.model_dump(mode="json"),
            raw_data={"original_request": data.model_dump(mode="json")},
            timeline=[],
        )
        
        self.session.add(incident_orm)
        await self.session.flush()
        await self.session.refresh(incident_orm)
        
        return self._to_model(incident_orm)
    
    async def get_by_id(self, incident_id: UUID) -> Incident:
        """Get incident by ID.
        
        Raises:
            IncidentNotFoundError: If incident not found
        """
        stmt = select(IncidentORM).where(IncidentORM.id == incident_id)
        result = await self.session.execute(stmt)
        incident_orm = result.scalar_one_or_none()
        
        if incident_orm is None:
            raise IncidentNotFoundError(str(incident_id))
        
        return self._to_model(incident_orm)
    
    async def get_by_id_or_none(self, incident_id: UUID) -> Optional[Incident]:
        """Get incident by ID, returns None if not found."""
        try:
            return await self.get_by_id(incident_id)
        except IncidentNotFoundError:
            return None
    
    async def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IncidentSummary]:
        """List incidents with optional filters."""
        stmt = select(IncidentORM).order_by(IncidentORM.created_at.desc())
        
        if status:
            stmt = stmt.where(IncidentORM.status == status)
        if severity:
            stmt = stmt.where(IncidentORM.severity == severity)
        
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        incidents = result.scalars().all()
        
        return [
            IncidentSummary(
                id=i.id,
                title=i.title,
                severity=i.severity,
                status=i.status,
                created_at=i.created_at,
            )
            for i in incidents
        ]
    
    async def update(self, incident_id: UUID, data: IncidentUpdate) -> Incident:
        """Update incident fields."""
        updates = {}
        
        if data.status is not None:
            updates["status"] = data.status
        if data.current_state is not None:
            updates["current_state"] = data.current_state
        if data.error_message is not None:
            updates["error_message"] = data.error_message
        
        updates["updated_at"] = datetime.utcnow()
        
        stmt = (
            update(IncidentORM)
            .where(IncidentORM.id == incident_id)
            .values(**updates)
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(incident_id)
    
    async def update_status(
        self,
        incident_id: UUID,
        status: IncidentStatus,
        error_message: Optional[str] = None,
    ) -> Incident:
        """Update incident status."""
        return await self.update(
            incident_id,
            IncidentUpdate(status=status, error_message=error_message),
        )
    
    async def add_timeline_event(
        self,
        incident_id: UUID,
        state: str,
        details: Optional[dict] = None,
    ) -> Incident:
        """Add an event to the incident timeline."""
        incident = await self.get_by_id(incident_id)
        
        event = TimelineEvent(
            state=state,
            timestamp=datetime.utcnow(),
            details=details,
        )
        
        new_timeline = incident.timeline + [event]
        
        stmt = (
            update(IncidentORM)
            .where(IncidentORM.id == incident_id)
            .values(
                timeline=[e.model_dump(mode="json") for e in new_timeline],
                current_state=state,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(incident_id)
    
    async def set_pr_url(self, incident_id: UUID, pr_url: str) -> Incident:
        """Set the PR URL for an incident."""
        stmt = (
            update(IncidentORM)
            .where(IncidentORM.id == incident_id)
            .values(pr_url=pr_url, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(incident_id)
    
    async def count_by_status(self, status: IncidentStatus) -> int:
        """Count incidents by status."""
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(IncidentORM).where(
            IncidentORM.status == status
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    def _to_model(self, orm: IncidentORM) -> Incident:
        """Convert ORM model to Pydantic model."""
        metadata_dict = orm.incident_metadata or {}
        repo_data = metadata_dict.get("repository", {})
        
        return Incident(
            id=orm.id,
            title=orm.title,
            description=orm.description,
            severity=orm.severity,
            source=orm.source,
            status=orm.status,
            current_state=orm.current_state,
            error_message=orm.error_message,
            logs=orm.logs,
            raw_data=orm.raw_data or {},
            metadata=IncidentMetadata(
                repository=RepositoryInfo(**repo_data) if repo_data else RepositoryInfo(url=""),
                triggered_by=metadata_dict.get("triggered_by"),
                workflow_name=metadata_dict.get("workflow_name"),
                job_url=metadata_dict.get("job_url"),
                alert_id=metadata_dict.get("alert_id"),
                tags=metadata_dict.get("tags", []),
            ),
            timeline=[TimelineEvent(**e) for e in (orm.timeline or [])],
            pr_url=orm.pr_url,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
