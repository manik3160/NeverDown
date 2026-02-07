"""Audit log repository for data access."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AuditLogORM


class AuditRepository:
    """Repository for audit log data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        incident_id: Optional[UUID] = None,
    ) -> UUID:
        """Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'state_transition', 'agent_execution')
            event_data: Event details as dictionary
            incident_id: Optional related incident ID
            
        Returns:
            ID of the created audit log entry
        """
        log_entry = AuditLogORM(
            id=uuid4(),
            incident_id=incident_id,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.utcnow(),
        )
        
        self.session.add(log_entry)
        await self.session.flush()
        
        return log_entry.id
    
    async def log_state_transition(
        self,
        incident_id: UUID,
        from_state: str,
        to_state: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Log a state machine transition."""
        return await self.log_event(
            event_type="state_transition",
            event_data={
                "from_state": from_state,
                "to_state": to_state,
                "metadata": metadata or {},
            },
            incident_id=incident_id,
        )
    
    async def log_agent_execution(
        self,
        incident_id: UUID,
        agent_name: str,
        action: str,
        success: bool,
        duration_ms: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Log an agent execution event."""
        return await self.log_event(
            event_type="agent_execution",
            event_data={
                "agent": agent_name,
                "action": action,
                "success": success,
                "duration_ms": duration_ms,
                "metadata": metadata or {},
            },
            incident_id=incident_id,
        )
    
    async def log_api_call(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: int,
        client_ip: Optional[str] = None,
        incident_id: Optional[UUID] = None,
    ) -> UUID:
        """Log an API request."""
        return await self.log_event(
            event_type="api_call",
            event_data={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            },
            incident_id=incident_id,
        )
    
    async def log_security_event(
        self,
        event_name: str,
        severity: str,
        details: Dict[str, Any],
        incident_id: Optional[UUID] = None,
    ) -> UUID:
        """Log a security-related event."""
        return await self.log_event(
            event_type="security_event",
            event_data={
                "event_name": event_name,
                "severity": severity,
                "details": details,
            },
            incident_id=incident_id,
        )
    
    async def get_by_incident(
        self,
        incident_id: UUID,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit logs for an incident."""
        stmt = (
            select(AuditLogORM)
            .where(AuditLogORM.incident_id == incident_id)
            .order_by(AuditLogORM.timestamp.desc())
        )
        
        if event_type:
            stmt = stmt.where(AuditLogORM.event_type == event_type)
        
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "event_data": log.event_data,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]
    
    async def get_recent_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent audit events across all incidents."""
        stmt = select(AuditLogORM).order_by(AuditLogORM.timestamp.desc())
        
        if event_type:
            stmt = stmt.where(AuditLogORM.event_type == event_type)
        
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        return [
            {
                "id": str(log.id),
                "incident_id": str(log.incident_id) if log.incident_id else None,
                "event_type": log.event_type,
                "event_data": log.event_data,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]
