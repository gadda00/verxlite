"""
Artifact Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ArtifactType(str, Enum):
    """Artifact type enum."""
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


class ArtifactStatus(str, Enum):
    """Artifact status enum."""
    CREATED = "created"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class ArtifactResponse(BaseModel):
    """Artifact response model."""
    id: str
    run_id: str
    artifact_type: ArtifactType
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    status: ArtifactStatus
    content_summary: Optional[str] = None
    content_data: Dict[str, Any]
    extra_metadata: Dict[str, Any]
    parent_artifact_id: Optional[str] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    file_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "artifact_abc123",
                "run_id": "run_abc123",
                "artifact_type": "crm_note",
                "external_url": "https://hubspot.com/note/123",
                "status": "completed",
                "content_summary": "Meeting summary",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class ArtifactListResponse(BaseModel):
    """List of artifacts response."""
    artifacts: List[ArtifactResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "artifacts": [
                    {
                        "id": "artifact_abc123",
                        "artifact_type": "crm_note",
                        "status": "completed"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100
            }
        }


class ArtifactCreate(BaseModel):
    """Artifact creation request."""
    run_id: str = Field(..., description="ID of workflow run")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    external_id: Optional[str] = Field(None, description="External ID")
    external_url: Optional[str] = Field(None, description="External URL")
    content_summary: Optional[str] = Field(None, description="Content summary")
    content_data: Dict[str, Any] = Field(default_factory=dict, description="Content data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    parent_artifact_id: Optional[str] = Field(None, description="Parent artifact ID")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_abc123",
                "artifact_type": "crm_note",
                "external_url": "https://hubspot.com/note/123",
                "content_summary": "Meeting summary"
            }
        }
