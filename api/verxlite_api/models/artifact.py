"""
Artifact Model
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from verxlite_api.db.base import BaseModel


class Artifact(BaseModel):
    """
    Represents an artifact created by a workflow (CRM note, email draft, task, etc.).
    """
    __tablename__ = "artifacts"

    run_id = Column(String(36), ForeignKey("workflow_runs.id"), nullable=False, index=True)
    
    # Artifact information
    artifact_type = Column(String(50), nullable=False)  # crm_note, email_draft, task, document
    external_id = Column(String(255), nullable=True)  # ID from the external system
    external_url = Column(Text, nullable=True)  # Deep link to the artifact
    
    # Content (sanitized)
    content_summary = Column(Text, nullable=True)
    content_data = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional artifact-specific data

    # Relationships
    workflow_run = relationship("WorkflowRun")

    def __repr__(self):
        return f"<Artifact(id={self.id}, type={self.artifact_type}, run_id={self.run_id})>"
