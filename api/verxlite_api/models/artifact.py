"""
Artifact Model
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, Index, Enum, Integer
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from verxlite_api.db.base import BaseModel


class ArtifactType(PyEnum):
    """Type of artifact."""
    CRM_NOTE = "crm_note"
    CRM_TASK = "crm_task"
    CRM_DEAL = "crm_deal"
    CRM_CONTACT = "crm_contact"
    CRM_COMPANY = "crm_company"
    EMAIL_DRAFT = "email_draft"
    EMAIL_SENT = "email_sent"
    DOCUMENT = "document"
    FILE = "file"
    SUMMARY = "summary"
    REPORT = "report"
    LOG = "log"
    OTHER = "other"


class ArtifactStatus(PyEnum):
    """Status of an artifact."""
    CREATED = "created"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class Artifact(BaseModel):
    """
    Represents an artifact created by a workflow (CRM note, email draft, task, etc.).
    
    Attributes:
        run_id: Workflow run that created this artifact
        artifact_type: Type of artifact (from ArtifactType enum)
        external_id: ID from the external system
        external_url: Deep link to the artifact
        status: Current status of the artifact
        content_summary: Sanitized summary of content
        content_data: Full content data (JSON)
        metadata: Additional metadata for the artifact
        parent_artifact_id: ID of parent artifact if this is a child
        size_bytes: Size of the artifact in bytes (for files)
        mime_type: MIME type of the artifact (for files)
    """
    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifact_run", "run_id"),
        Index("ix_artifact_type", "artifact_type"),
        Index("ix_artifact_external_id", "external_id"),
        Index("ix_artifact_status", "status"),
        Index("ix_artifact_created", "created_at"),
    )

    run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Artifact information
    artifact_type = Column(
        Enum(ArtifactType, name="artifact_type_enum", create_type=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    external_id = Column(String(255), nullable=True)  # ID from the external system
    external_url = Column(Text, nullable=True)  # Deep link to the artifact
    status = Column(
        Enum(ArtifactStatus, name="artifact_status_enum", create_type=True, values_callable=lambda x: [e.value for e in x]),
        default=ArtifactStatus.CREATED,
        nullable=False
    )
    
    # Content (sanitized)
    content_summary = Column(Text, nullable=True)
    content_data = Column(JSON, nullable=True, default=dict)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True, default=dict)
    
    # Hierarchy
    parent_artifact_id = Column(String(36), ForeignKey("artifacts.id"), nullable=True)
    
    # File information (for file artifacts)
    size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_name = Column(String(255), nullable=True)

    # Relationships
    # `workflow_run` is created via backref on WorkflowRun.artifacts.
    # NOTE: self-referential parent_artifact / child_artifacts omitted (see WorkflowRun note).

    @property
    def is_file(self) -> bool:
        """Check if this is a file artifact."""
        return self.artifact_type in [
            ArtifactType.DOCUMENT,
            ArtifactType.FILE,
        ]

    @property
    def is_crm(self) -> bool:
        """Check if this is a CRM artifact."""
        return self.artifact_type.value.startswith("crm_")

    @property
    def is_email(self) -> bool:
        """Check if this is an email artifact."""
        return self.artifact_type in [
            ArtifactType.EMAIL_DRAFT,
            ArtifactType.EMAIL_SENT,
        ]

    def to_dict(self):
        """Convert artifact to dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "artifact_type": self.artifact_type.value,
            "external_id": self.external_id,
            "external_url": self.external_url,
            "status": self.status.value,
            "content_summary": self.content_summary,
            "content_data": self.content_data,
            "metadata": self.extra_metadata,
            "parent_artifact_id": self.parent_artifact_id,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "file_name": self.file_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<Artifact(id={self.id}, type={self.artifact_type.value}, run_id={self.run_id}, status={self.status.value})>"
