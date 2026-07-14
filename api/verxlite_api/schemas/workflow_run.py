"""
Workflow Run Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowRunTriggerType(str, Enum):
    """Workflow run trigger type enum."""
    MANUAL = "manual"
    CALENDAR_EVENT_ENDED = "calendar_event_ended"
    CALENDAR_EVENT_STARTED = "calendar_event_started"
    EMAIL_RECEIVED = "email_received"
    EMAIL_SENT = "email_sent"
    CRM_EVENT = "crm_event"
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    API_CALL = "api_call"


class WorkflowRunStatus(str, Enum):
    """Workflow run status enum."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class WorkflowRunCreate(BaseModel):
    """Workflow run creation request. `workflow_id` is taken from the URL path."""
    trigger_type: WorkflowRunTriggerType = Field(
        WorkflowRunTriggerType.MANUAL,
        description="Type of trigger"
    )
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="Trigger data")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule run for later")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow_abc123",
                "trigger_type": "manual",
                "trigger_data": {"event_id": "event_123"},
                "idempotency_key": "unique_key_123"
            }
        }


class WorkflowRunResponse(BaseModel):
    """Workflow run response model."""
    id: str
    tenant_id: str
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    trigger_type: WorkflowRunTriggerType
    trigger_data: Dict[str, Any]
    status: WorkflowRunStatus
    error_message: Optional[str] = None
    total_tokens: int
    total_duration_ms: int
    total_cost: float
    idempotency_key: Optional[str] = None
    parent_run_id: Optional[str] = None
    retry_count: int
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "run_abc123",
                "tenant_id": "tenant_abc123",
                "workflow_id": "workflow_abc123",
                "trigger_type": "manual",
                "status": "completed",
                "total_tokens": 1500,
                "total_duration_ms": 2500,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class WorkflowRunDetailResponse(WorkflowRunResponse):
    """Workflow run detail response with steps and artifacts."""
    steps: List[dict] = Field(default_factory=list, description="Workflow steps")
    artifacts: List[dict] = Field(default_factory=list, description="Artifacts created")
    workflow: Optional[dict] = Field(None, description="Workflow details")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "run_abc123",
                "status": "completed",
                "steps": [
                    {
                        "id": "step_1",
                        "step_type": "tool",
                        "step_name": "Fetch calendar event",
                        "status": "completed",
                        "latency_ms": 500
                    }
                ],
                "artifacts": [
                    {
                        "id": "artifact_1",
                        "artifact_type": "crm_note",
                        "external_url": "https://hubspot.com/note/123"
                    }
                ]
            }
        }


class WorkflowRunListResponse(BaseModel):
    """List of workflow runs response."""
    runs: List[WorkflowRunResponse]
    total: int
    page: int = 1
    page_size: int = 100

    class Config:
        json_schema_extra = {
            "example": {
                "runs": [
                    {
                        "id": "run_abc123",
                        "status": "completed",
                        "total_tokens": 1500
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100
            }
        }


class WorkflowRunStatsResponse(BaseModel):
    """Workflow run statistics response."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    total_tokens: int
    avg_duration_ms: float
    p50_duration_ms: float
    p90_duration_ms: float
    runs_by_workflow: Dict[str, int] = Field(default_factory=dict)
    runs_by_status: Dict[str, int] = Field(default_factory=dict)
    runs_by_trigger: Dict[str, int] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "total_runs": 100,
                "successful_runs": 95,
                "failed_runs": 5,
                "success_rate": 0.95,
                "total_tokens": 50000,
                "avg_duration_ms": 1800.0
            }
        }
