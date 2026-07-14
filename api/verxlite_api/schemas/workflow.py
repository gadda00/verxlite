"""
Workflow Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Workflow type enum."""

    POST_MEETING_FOLLOWUP = "post_meeting_followup"
    LEAD_ASSIGNMENT = "lead_assignment"
    SUPPORT_TRIAGE = "support_triage"
    APPROVAL_WORKFLOW = "approval_workflow"
    WEEKLY_SUMMARY = "weekly_summary"
    CUSTOM = "custom"


class WorkflowStatus(str, Enum):
    """Workflow status enum."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowCreate(BaseModel):
    """Workflow creation request."""

    name: str = Field(..., description="Workflow name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Workflow description", max_length=5000)
    workflow_type: WorkflowType = Field(
        WorkflowType.POST_MEETING_FOLLOWUP, description="Type of workflow"
    )
    config: dict[str, Any] | None = Field(None, description="Workflow configuration")
    trigger_config: dict[str, Any] | None = Field(None, description="Trigger configuration")
    priority: int | None = Field(5, description="Priority (1-10)", ge=1, le=10)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Post-Meeting Followup",
                "description": "Auto-log to CRM + draft follow-up email + create tasks",
                "workflow_type": "post_meeting_followup",
                "config": {"create_crm_note": True, "draft_email": True, "create_task": True},
                "priority": 5,
            }
        }


class WorkflowUpdate(BaseModel):
    """Workflow update request."""

    name: str | None = Field(None, description="Workflow name", min_length=1, max_length=255)
    description: str | None = Field(None, description="Workflow description", max_length=5000)
    config: dict[str, Any] | None = Field(None, description="Workflow configuration")
    trigger_config: dict[str, Any] | None = Field(None, description="Trigger configuration")
    is_active: bool | None = Field(None, description="Whether workflow is active")
    status: WorkflowStatus | None = Field(None, description="Workflow status")
    priority: int | None = Field(None, description="Priority (1-10)", ge=1, le=10)

    class Config:
        json_schema_extra = {
            "example": {"name": "Post-Meeting Followup Updated", "is_active": True, "priority": 8}
        }


class WorkflowResponse(BaseModel):
    """Workflow response model."""

    id: str
    tenant_id: str
    created_by: str | None = None
    name: str
    description: str | None = None
    workflow_type: WorkflowType
    config: dict[str, Any]
    is_active: bool
    status: WorkflowStatus
    trigger_config: dict[str, Any]
    template_id: str | None = None
    version: str
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "workflow_abc123",
                "tenant_id": "tenant_abc123",
                "name": "Post-Meeting Followup",
                "workflow_type": "post_meeting_followup",
                "is_active": True,
                "status": "active",
                "version": "1.0",
                "priority": 5,
            }
        }


class WorkflowListResponse(BaseModel):
    """List of workflows response."""

    workflows: list[WorkflowResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "workflows": [
                    {
                        "id": "workflow_abc123",
                        "name": "Post-Meeting Followup",
                        "workflow_type": "post_meeting_followup",
                        "is_active": True,
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100,
            }
        }


class WorkflowTemplateResponse(BaseModel):
    """Workflow template response."""

    id: str
    name: str
    description: str
    workflow_type: WorkflowType
    default_config: dict[str, Any]
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "template_abc123",
                "name": "Post-Meeting Followup Template",
                "workflow_type": "post_meeting_followup",
                "default_config": {"create_crm_note": True, "draft_email": True},
            }
        }


class WorkflowTemplateListResponse(BaseModel):
    """List of workflow templates response."""

    templates: list[WorkflowTemplateResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "templates": [{"id": "template_abc123", "name": "Post-Meeting Followup Template"}],
                "total": 1,
            }
        }
