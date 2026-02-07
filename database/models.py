"""SQLAlchemy ORM models for NeverDown."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base
from models.incident import IncidentSeverity, IncidentSource, IncidentStatus
from models.pull_request import PRStatus
from models.verification import VerificationStatus


class IncidentORM(Base):
    """Incident database table."""
    
    __tablename__ = "incidents"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[IncidentSeverity] = mapped_column(
        SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM
    )
    source: Mapped[IncidentSource] = mapped_column(
        SQLEnum(IncidentSource), default=IncidentSource.MANUAL
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(IncidentStatus), default=IncidentStatus.PENDING
    )
    current_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, name="metadata_json")
    timeline: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    pr_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    analyses: Mapped[List["AnalysisORM"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    patches: Mapped[List["PatchORM"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    pull_requests: Mapped[List["PullRequestORM"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLogORM"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )


class AnalysisORM(Base):
    """Analysis database table."""
    
    __tablename__ = "analyses"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    output: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident: Mapped["IncidentORM"] = relationship(back_populates="analyses")


class PatchORM(Base):
    """Patch database table."""
    
    __tablename__ = "patches"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    diff: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    assumptions: Mapped[List[str]] = mapped_column(JSONB, default=list)
    files_changed: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    token_usage: Mapped[Optional[Dict[str, int]]] = mapped_column(JSONB, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident: Mapped["IncidentORM"] = relationship(back_populates="patches")
    verifications: Mapped[List["VerificationORM"]] = relationship(
        back_populates="patch", cascade="all, delete-orphan"
    )


class VerificationORM(Base):
    """Verification database table."""
    
    __tablename__ = "verifications"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patch_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patches.id", ondelete="CASCADE"), nullable=False
    )
    incident_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    test_results: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_failed: Mapped[int] = mapped_column(Integer, default=0)
    tests_skipped: Mapped[int] = mapped_column(Integer, default=0)
    sandbox_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    test_output: Mapped[str] = mapped_column(Text, default="")
    patch_applied_cleanly: Mapped[bool] = mapped_column(Boolean, default=True)
    health_check_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    patch: Mapped["PatchORM"] = relationship(back_populates="verifications")


class PullRequestORM(Base):
    """Pull request database table."""
    
    __tablename__ = "pull_requests"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    patch_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    verification_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    pr_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pr_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    base_branch: Mapped[str] = mapped_column(String(100), default="main")
    
    title: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    labels: Mapped[List[str]] = mapped_column(JSONB, default=list)
    
    status: Mapped[PRStatus] = mapped_column(SQLEnum(PRStatus), default=PRStatus.PENDING)
    merge_commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    github_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    incident: Mapped["IncidentORM"] = relationship(back_populates="pull_requests")


class AuditLogORM(Base):
    """Audit log database table."""
    
    __tablename__ = "audit_log"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    incident: Mapped[Optional["IncidentORM"]] = relationship(back_populates="audit_logs")
