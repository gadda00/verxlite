"""
Workflow Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from verxlite_api.db.base import BaseModel


class Workflow(BaseModel):
    """
    Represents a workflow definition.
    """
    __tablename__ = "workflows"

    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(String(50), nullable=False)  # e.g., post_meeting_followup
    config = Column(JSON, nullable=True)  # Workflow-specific configuration
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    tenant = relationship("Tenant", backref="workflows")
    runs = relationship("WorkflowRun", backref="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, type={self.workflow_type})>"
