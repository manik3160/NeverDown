"""Patch repository for data access."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import PatchNotFoundError
from database.models import PatchORM
from models.patch import FileChange, Patch, PatchCreate


class PatchRepository:
    """Repository for patch data access operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: PatchCreate) -> Patch:
        """Create a new patch."""
        patch_orm = PatchORM(
            incident_id=data.incident_id,
            diff=data.diff,
            reasoning=data.reasoning,
            confidence=data.confidence,
            assumptions=data.assumptions,
            token_usage=data.token_usage,
            files_changed=[],
        )
        
        self.session.add(patch_orm)
        await self.session.flush()
        await self.session.refresh(patch_orm)
        
        return self._to_model(patch_orm)
    
    async def get_by_id(self, patch_id: UUID) -> Patch:
        """Get patch by ID.
        
        Raises:
            PatchNotFoundError: If patch not found
        """
        stmt = select(PatchORM).where(PatchORM.id == patch_id)
        result = await self.session.execute(stmt)
        patch_orm = result.scalar_one_or_none()
        
        if patch_orm is None:
            raise PatchNotFoundError(str(patch_id))
        
        return self._to_model(patch_orm)
    
    async def get_by_incident_id(self, incident_id: UUID) -> List[Patch]:
        """Get all patches for an incident."""
        stmt = (
            select(PatchORM)
            .where(PatchORM.incident_id == incident_id)
            .order_by(PatchORM.created_at.desc())
        )
        result = await self.session.execute(stmt)
        patches = result.scalars().all()
        
        return [self._to_model(p) for p in patches]
    
    async def get_latest_for_incident(self, incident_id: UUID) -> Optional[Patch]:
        """Get the most recent patch for an incident."""
        patches = await self.get_by_incident_id(incident_id)
        return patches[0] if patches else None
    
    async def mark_verified(
        self,
        patch_id: UUID,
        verified: bool,
        verification_id: Optional[UUID] = None,
    ) -> Patch:
        """Mark a patch as verified or not."""
        updates = {"verified": verified}
        if verification_id:
            updates["verification_id"] = verification_id
        
        stmt = (
            update(PatchORM)
            .where(PatchORM.id == patch_id)
            .values(**updates)
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(patch_id)
    
    async def increment_retry_count(self, patch_id: UUID) -> Patch:
        """Increment the retry count for a patch."""
        patch = await self.get_by_id(patch_id)
        
        stmt = (
            update(PatchORM)
            .where(PatchORM.id == patch_id)
            .values(retry_count=patch.retry_count + 1)
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(patch_id)
    
    async def update_files_changed(
        self,
        patch_id: UUID,
        files_changed: List[FileChange],
    ) -> Patch:
        """Update the files changed for a patch."""
        stmt = (
            update(PatchORM)
            .where(PatchORM.id == patch_id)
            .values(files_changed=[f.model_dump() for f in files_changed])
        )
        await self.session.execute(stmt)
        
        return await self.get_by_id(patch_id)
    
    def _to_model(self, orm: PatchORM) -> Patch:
        """Convert ORM model to Pydantic model."""
        files = [FileChange(**f) for f in (orm.files_changed or [])]
        
        return Patch(
            id=orm.id,
            incident_id=orm.incident_id,
            diff=orm.diff,
            reasoning=orm.reasoning,
            confidence=orm.confidence,
            assumptions=orm.assumptions or [],
            files_changed=files,
            verified=orm.verified,
            token_usage=orm.token_usage,
            retry_count=orm.retry_count,
            created_at=orm.created_at,
        )
