"""
WorkflowRun Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, Float, DateTime, Index, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from verxlite_api.db.base import BaseModel


class WorkflowRunStatus(PyEnum):
    """Status of a workflow run."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowRunTriggerType(PyEnum):
    """Type of trigger for a workflow run."""
    MANUAL = "manual"
    CALENDAR_EVENT_ENDED = "calendar_event_ended"
    CALENDAR_EVENT_STARTED = "calendar_event_started"
    EMAIL_RECEIVED = "email_received"
    EMAIL_SENT = "email_sent"
    CRM_EVENT = "crm_event"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    API_CALL = "api_call"


class WorkflowRun(BaseModel):
    """
    Represents a single execution of a workflow.
    
    Attributes:
        tenant_id: Tenant this run belongs to
        user_id: User who triggered this run
        workflow_id: Workflow that was executed
        trigger_type: Type of trigger (from WorkflowRunTriggerType enum)
        trigger_data: Data associated with the trigger
        status: Current status of the run
        error_message: Error message if run failed
        total_tokens: Total tokens used by LLM calls
        total_duration_ms: Total duration in milliseconds
        total_cost: Total cost of the run
        idempotency_key: Unique key to prevent duplicate runs
        parent_run_id: ID of parent run if this is a retry
        retry_count: Number of times this run has been retried
        scheduled_for: When the run is scheduled to execute
        started_at: When the run started
        completed_at: When the run completed
        metadata: Additional metadata for the run
    """
    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index("ix_workflow_run_tenant", "tenant_id"),
        Index("ix_workflow_run_user", "user_id"),
        Index("ix_workflow_run_workflow", "workflow_id"),
        Index("ix_workflow_run_status", "status"),
        Index("ix_workflow_run_trigger", "trigger_type"),
        Index("ix_workflow_run_idempotency", "idempotency_key", unique=True),
        Index("ix_workflow_run_created", "created_at"),
        Index("ix_workflow_run_scheduled", "scheduled_for"),
    )

    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True)
    
    # Trigger information
    trigger_type = Column(
        Enum(WorkflowRunTriggerType, name="workflow_run_trigger_type_enum", create_type=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    trigger_data = Column(JSON, nullable=True, default=dict)  # e.g., {event_id: 'abc123'}
    
    # Execution status
    status = Column(
        Enum(WorkflowRunStatus, name="workflow_run_status_enum", create_type=True, values_callable=lambda x: [e.value for e in x]),
        default=WorkflowRunStatus.PENDING,
        nullable=False
    )
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    
    # Performance metrics
    total_tokens = Column(Integer, default=0, nullable=False)
    total_duration_ms = Column(Integer, default=0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    
    # Idempotency
    idempotency_key = Column(String(255), nullable=True, unique=True)
    
    # Retry information
    parent_run_id = Column(String(36), ForeignKey("workflow_runs.id"), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Timing
    scheduled_for = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    tenant = relationship("Tenant")
    # `user` is created via backref on User.workflow_runs.
    # `workflow` is created via backref on Workflow.runs.
    # NOTE: self-referential parent_run / child_runs omitted to avoid SQLAlchemy
    # 2.x remote_side string-resolution issues with the inherited `id` column
    # (which collides with Python's builtin `id`). Query child runs explicitly
    # via `db.query(WorkflowRun).filter(WorkflowRun.parent_run_id == run.id)`.
    steps = relationship("WorkflowStep", backref="workflow_run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", backref="workflow_run", cascade="all, delete-orphan")

    @property
    def is_completed(self) -> bool:
        """Check if run is completed (successfully or with failure)."""
        return self.status in [
            WorkflowRunStatus.COMPLETED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
            WorkflowRunStatus.TIMEOUT,
        ]

    @property
    def is_active(self) -> bool:
        """Check if run is currently active."""
        return self.status in [
            WorkflowRunStatus.PENDING,
            WorkflowRunStatus.QUEUED,
            WorkflowRunStatus.RUNNING,
        ]

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.total_duration_ms / 1000.0

    def to_dict(self):
        """Convert workflow run to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "trigger_type": self.trigger_type.value,
            "trigger_data": self.trigger_data,
            "status": self.status.value,
            "error_message": self.error_message,
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "total_cost": self.total_cost,
            "idempotency_key": self.idempotency_key,
            "parent_run_id": self.parent_run_id,
            "retry_count": self.retry_count,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, workflow_id={self.workflow_id}, status={self.status.value}, trigger_type={self.trigger_type.value})>"
