"""
WorkflowStep Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, DateTime, Index, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from verxlite_api.db.base import BaseModel


class WorkflowStepStatus(PyEnum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class WorkflowStepType(PyEnum):
    """Type of workflow step."""
    TRIGGER = "trigger"
    LLM = "llm"
    TOOL = "tool"
    PARALLEL = "parallel"
    BRANCH = "branch"
    CONDITIONAL = "conditional"
    WAIT = "wait"
    LOOP = "loop"


class WorkflowStep(BaseModel):
    """
    Represents a single step in a workflow run.
    
    Attributes:
        run_id: Workflow run this step belongs to
        step_type: Type of step (from WorkflowStepType enum)
        step_name: Human-readable name of the step
        tool_name: Name of the tool if step_type is TOOL
        status: Current status of the step
        error_message: Error message if step failed
        input_summary: Sanitized summary of input (no PII)
        output_summary: Sanitized summary of output (no PII)
        input_data: Full input data (JSON)
        output_data: Full output data (JSON)
        latency_ms: Latency in milliseconds
        tokens_used: Number of tokens used (for LLM steps)
        order: Order of this step in the workflow
        retry_count: Number of times this step has been retried
        max_retries: Maximum number of retries for this step
        timeout_ms: Timeout for this step in milliseconds
        started_at: When the step started
        completed_at: When the step completed
        metadata: Additional metadata for the step
    """
    __tablename__ = "workflow_steps"
    __table_args__ = (
        Index("ix_workflow_step_run", "run_id"),
        Index("ix_workflow_step_type", "step_type"),
        Index("ix_workflow_step_status", "status"),
        Index("ix_workflow_step_order", "order"),
        Index("ix_workflow_step_tool", "tool_name"),
        Index("ix_workflow_step_created", "created_at"),
    )

    run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Step information
    step_type = Column(
        Enum(WorkflowStepType, name="workflow_step_type_enum", create_type=True),
        nullable=False
    )
    step_name = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=True)  # e.g., get_calendar_event, create_crm_note
    
    # Execution status
    status = Column(
        Enum(WorkflowStepStatus, name="workflow_step_status_enum", create_type=True),
        default=WorkflowStepStatus.PENDING,
        nullable=False
    )
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)
    
    # Input/Output (sanitized, no PII)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True, default={})
    output_data = Column(JSON, nullable=True, default={})
    
    # Performance metrics
    latency_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    
    # Order and flow control
    order = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    timeout_ms = Column(Integer, default=30000, nullable=False)  # 30 seconds default
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True, default={})

    @property
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self.status in [
            WorkflowStepStatus.COMPLETED,
            WorkflowStepStatus.FAILED,
            WorkflowStepStatus.SKIPPED,
            WorkflowStepStatus.TIMEOUT,
        ]

    @property
    def is_active(self) -> bool:
        """Check if step is currently active."""
        return self.status in [
            WorkflowStepStatus.PENDING,
            WorkflowStepStatus.RUNNING,
        ]

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.latency_ms:
            return self.latency_ms / 1000.0
        return 0.0

    def to_dict(self):
        """Convert workflow step to dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "step_type": self.step_type.value,
            "step_name": self.step_name,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "error_message": self.error_message,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "order": self.order,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_ms": self.timeout_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<WorkflowStep(id={self.id}, run_id={self.run_id}, step_type={self.step_type.value}, status={self.status.value}, order={self.order})>"
