"""
WorkflowRun Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import relationship
from verxlite_api.db.base import BaseModel


class WorkflowRun(BaseModel):
    """
    Represents a single execution of a workflow.
    """
    __tablename__ = "workflow_runs"

    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    
    # Trigger information
    trigger_type = Column(String(50), nullable=False)  # calendar_event_ended, manual, etc.
    trigger_data = Column(JSON, nullable=True)  # e.g., {event_id: 'abc123'}
    
    # Execution status
    status = Column(String(20), default="pending", nullable=False)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    total_tokens = Column(Integer, default=0, nullable=False)
    total_duration_ms = Column(Integer, default=0, nullable=False)
    total_cost = Column(Float, default=0.0, nullable=False)
    
    # Idempotency
    idempotency_key = Column(String(255), nullable=True, unique=True)

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    workflow = relationship("Workflow")
    steps = relationship("WorkflowStep", backref="workflow_run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", backref="workflow_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkflowRun(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"
