"""
Workflows Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import time

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.workflow import Workflow, WorkflowType, WorkflowStatus
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus, WorkflowRunTriggerType
from verxlite_api.models.workflow_step import WorkflowStep
from verxlite_api.models.artifact import Artifact
from verxlite_api.models.connection import Connection
from verxlite_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowTemplateResponse,
    WorkflowTemplateListResponse,
)
from verxlite_api.schemas.workflow_run import (
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowRunListResponse,
    WorkflowRunDetailResponse,
    WorkflowRunStatsResponse,
)
from verxlite_api.schemas.error import NotFoundErrorResponse, AuthorizationErrorResponse
from verxlite_api.utils.logger import get_logger
from verxlite_api.services.workflow_engine import WorkflowEngine
from verxlite_api.observability.langfuse import LangfuseTracer
from verxlite_api.observability.metrics import MetricsCollector

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = get_logger("workflows")


# Pagination parameters
class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    request: Request,
    db=Depends(get_db),
    pagination: PaginationParams = Depends(),
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by workflow type"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
):
    """
    List all workflows for the current tenant.
    
    Supports:
    - Pagination
    - Filtering by type, status, active status
    - Search in name and description
    """
    # Get current user from JWT (in production, use real auth)
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    query = db.query(Workflow).filter(Workflow.tenant_id == tenant_id)
    
    # Apply filters
    if workflow_type:
        query = query.filter(Workflow.workflow_type == workflow_type)
    
    if status:
        query = query.filter(Workflow.status == status)
    
    if is_active is not None:
        query = query.filter(Workflow.is_active == is_active)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Workflow.name.ilike(search_pattern)) |
            (Workflow.description.ilike(search_pattern))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    workflows = query.order_by(
        Workflow.priority.desc(),
        Workflow.name.asc()
    ).offset(pagination.offset).limit(pagination.page_size).all()
    
    return WorkflowListResponse(
        workflows=[WorkflowResponse.from_orm(wf) for wf in workflows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: Request,
    workflow_data: WorkflowCreate,
    db=Depends(get_db),
):
    """
    Create a new workflow.
    """
    # Get current user from JWT (in production, use real auth)
    tenant_id = "test-tenant-id"
    user_id = "test-user-id"
    
    # Check if workflow with same name already exists
    existing = db.query(Workflow).filter(
        Workflow.tenant_id == tenant_id,
        Workflow.name == workflow_data.name,
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with name '{workflow_data.name}' already exists",
        )
    
    # Create workflow
    workflow = Workflow(
        tenant_id=tenant_id,
        created_by=user_id,
        name=workflow_data.name,
        description=workflow_data.description,
        workflow_type=workflow_data.workflow_type,
        config=workflow_data.config or {},
        trigger_config=workflow_data.trigger_config or {},
        priority=workflow_data.priority or 5,
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"Created workflow: {workflow.id}")
    
    return WorkflowResponse.from_orm(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Get a specific workflow by ID.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    return WorkflowResponse.from_orm(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: Request,
    workflow_data: WorkflowUpdate,
    db=Depends(get_db),
):
    """
    Update a workflow.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    # Update fields
    if workflow_data.name is not None:
        workflow.name = workflow_data.name
    if workflow_data.description is not None:
        workflow.description = workflow_data.description
    if workflow_data.config is not None:
        workflow.config = workflow_data.config
    if workflow_data.trigger_config is not None:
        workflow.trigger_config = workflow_data.trigger_config
    if workflow_data.is_active is not None:
        workflow.is_active = workflow_data.is_active
    if workflow_data.status is not None:
        workflow.status = workflow_data.status
    if workflow_data.priority is not None:
        workflow.priority = workflow_data.priority
    
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"Updated workflow: {workflow.id}")
    
    return WorkflowResponse.from_orm(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Delete a workflow.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    # Soft delete (set is_active to False)
    workflow.is_active = False
    workflow.status = WorkflowStatus.ARCHIVED
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Deleted workflow: {workflow.id}")
    
    return None


@router.post("/{workflow_id}/runs", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_workflow_run(
    workflow_id: str,
    request: Request,
    run_data: WorkflowRunCreate,
    db=Depends(get_db),
):
    """
    Trigger a workflow run.
    
    This endpoint:
    - Creates a workflow run record
    - Adds it to the queue for processing
    - Returns the run ID for tracking
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    user_id = "test-user-id"  # Replace with real user ID from auth
    
    # Get workflow
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    if not workflow.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot run inactive workflow",
        )
    
    # Check for duplicate idempotency key
    if run_data.idempotency_key:
        existing_run = db.query(WorkflowRun).filter(
            WorkflowRun.idempotency_key == run_data.idempotency_key,
            WorkflowRun.tenant_id == tenant_id,
        ).first()
        
        if existing_run:
            logger.info(f"Duplicate run detected for idempotency key: {run_data.idempotency_key}")
            return WorkflowRunResponse.from_orm(existing_run)
    
    # Create workflow run
    run_id = str(uuid.uuid4())
    workflow_run = WorkflowRun(
        id=run_id,
        tenant_id=tenant_id,
        user_id=user_id,
        workflow_id=workflow_id,
        trigger_type=run_data.trigger_type,
        trigger_data=run_data.trigger_data or {},
        status=WorkflowRunStatus.PENDING,
        idempotency_key=run_data.idempotency_key or f"{workflow_id}_{run_data.trigger_type}_{int(time.time())}",
        scheduled_for=run_data.scheduled_for,
    )
    
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)
    
    # Add initial step
    step = WorkflowStep(
        run_id=run_id,
        step_type="trigger",
        step_name="Workflow triggered",
        status="completed",
        order=0,
        latency_ms=0,
        tokens_used=0,
    )
    db.add(step)
    db.commit()
    
    # In production, add to queue here
    # from verxlite_api.tasks import execute_workflow_run
    # execute_workflow_run.delay(
    #     workflow_id=workflow_id,
    #     tenant_id=tenant_id,
    #     user_id=user_id,
    #     trigger_type=run_data.trigger_type.value,
    #     trigger_data=run_data.trigger_data or {},
    # )
    
    # For now, mark as queued
    workflow_run.status = WorkflowRunStatus.QUEUED
    db.commit()
    
    logger.info(f"Triggered workflow run: {run_id}")
    
    return WorkflowRunResponse.from_orm(workflow_run)


@router.get("/runs/{run_id}", response_model=WorkflowRunDetailResponse)
async def get_workflow_run(
    run_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Get details of a workflow run including steps and artifacts.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow_run = db.query(WorkflowRun).filter(
        WorkflowRun.id == run_id,
        WorkflowRun.tenant_id == tenant_id,
    ).first()
    
    if not workflow_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run not found: {run_id}",
        )
    
    # Get steps
    steps = db.query(WorkflowStep).filter(
        WorkflowStep.run_id == run_id
    ).order_by(WorkflowStep.order.asc()).all()
    
    # Get artifacts
    artifacts = db.query(Artifact).filter(
        Artifact.run_id == run_id
    ).all()
    
    # Get workflow
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_run.workflow_id
    ).first()
    
    return WorkflowRunDetailResponse(
        **WorkflowRunResponse.from_orm(workflow_run).model_dump(),
        steps=[step.to_dict() for step in steps],
        artifacts=[artifact.to_dict() for artifact in artifacts],
        workflow=workflow.to_dict() if workflow else None,
    )


@router.get("/runs", response_model=WorkflowRunListResponse)
async def list_workflow_runs(
    request: Request,
    db=Depends(get_db),
    pagination: PaginationParams = Depends(),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    status: Optional[WorkflowRunStatus] = Query(None, description="Filter by status"),
    trigger_type: Optional[WorkflowRunTriggerType] = Query(None, description="Filter by trigger type"),
    search: Optional[str] = Query(None, description="Search in trigger data"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
):
    """
    List workflow runs with optional filters.
    
    Supports:
    - Pagination
    - Filtering by workflow, status, trigger type, date range
    - Search in trigger data
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    query = db.query(WorkflowRun).filter(WorkflowRun.tenant_id == tenant_id)
    
    # Apply filters
    if workflow_id:
        query = query.filter(WorkflowRun.workflow_id == workflow_id)
    
    if status:
        query = query.filter(WorkflowRun.status == status)
    
    if trigger_type:
        query = query.filter(WorkflowRun.trigger_type == trigger_type)
    
    if start_date:
        query = query.filter(WorkflowRun.created_at >= start_date)
    
    if end_date:
        query = query.filter(WorkflowRun.created_at <= end_date)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    workflow_runs = query.order_by(
        WorkflowRun.created_at.desc()
    ).offset(pagination.offset).limit(pagination.page_size).all()
    
    return WorkflowRunListResponse(
        runs=[WorkflowRunResponse.from_orm(run) for run in workflow_runs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/stats", response_model=WorkflowRunStatsResponse)
async def get_workflow_stats(
    request: Request,
    db=Depends(get_db),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
):
    """
    Get workflow run statistics.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    query = db.query(WorkflowRun).filter(WorkflowRun.tenant_id == tenant_id)
    
    if workflow_id:
        query = query.filter(WorkflowRun.workflow_id == workflow_id)
    
    if start_date:
        query = query.filter(WorkflowRun.created_at >= start_date)
    
    if end_date:
        query = query.filter(WorkflowRun.created_at <= end_date)
    
    workflow_runs = query.all()
    
    # Calculate statistics
    total_runs = len(workflow_runs)
    successful_runs = sum(1 for run in workflow_runs if run.status == WorkflowRunStatus.COMPLETED)
    failed_runs = sum(1 for run in workflow_runs if run.status == WorkflowRunStatus.FAILED)
    success_rate = successful_runs / total_runs if total_runs > 0 else 0.0
    total_tokens = sum(run.total_tokens for run in workflow_runs)
    
    # Calculate duration statistics
    durations = [run.total_duration_ms for run in workflow_runs if run.total_duration_ms > 0]
    avg_duration_ms = sum(durations) / len(durations) if durations else 0.0
    
    if durations:
        sorted_durations = sorted(durations)
        p50_index = len(sorted_durations) // 2
        p90_index = int(len(sorted_durations) * 0.9)
        p50_duration_ms = sorted_durations[p50_index]
        p90_duration_ms = sorted_durations[min(p90_index, len(sorted_durations) - 1)]
    else:
        p50_duration_ms = 0.0
        p90_duration_ms = 0.0
    
    # Group by workflow
    runs_by_workflow = {}
    for run in workflow_runs:
        workflow_id = run.workflow_id or "unknown"
        runs_by_workflow[workflow_id] = runs_by_workflow.get(workflow_id, 0) + 1
    
    # Group by status
    runs_by_status = {}
    for run in workflow_runs:
        runs_by_status[run.status.value] = runs_by_status.get(run.status.value, 0) + 1
    
    # Group by trigger
    runs_by_trigger = {}
    for run in workflow_runs:
        runs_by_trigger[run.trigger_type.value] = runs_by_trigger.get(run.trigger_type.value, 0) + 1
    
    return WorkflowRunStatsResponse(
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        success_rate=success_rate,
        total_tokens=total_tokens,
        avg_duration_ms=avg_duration_ms,
        p50_duration_ms=p50_duration_ms,
        p90_duration_ms=p90_duration_ms,
        runs_by_workflow=runs_by_workflow,
        runs_by_status=runs_by_status,
        runs_by_trigger=runs_by_trigger,
    )


@router.get("/templates", response_model=WorkflowTemplateListResponse)
async def list_workflow_templates(
    request: Request,
    db=Depends(get_db),
):
    """
    List available workflow templates.
    """
    # In production, this would come from the database
    # For now, return hardcoded templates
    templates = [
        WorkflowTemplateResponse(
            id="template_post_meeting_followup",
            name="Post-Meeting Followup",
            description="Auto-log to CRM + draft follow-up email + create tasks after a meeting",
            workflow_type=WorkflowType.POST_MEETING_FOLLOWUP,
            default_config={
                "create_crm_note": True,
                "draft_email": True,
                "create_task": True,
                "email_template": "followup",
                "note_template": "summary",
                "task_due_days": 2,
            },
            created_at=datetime.utcnow(),
        ),
        WorkflowTemplateResponse(
            id="template_lead_assignment",
            name="Lead Assignment",
            description="Assign new leads to reps with automated follow-up sequence",
            workflow_type=WorkflowType.LEAD_ASSIGNMENT,
            default_config={
                "assign_to": "round_robin",
                "followup_sequence": [1, 3, 7],
                "notification_enabled": True,
            },
            created_at=datetime.utcnow(),
        ),
        WorkflowTemplateResponse(
            id="template_support_triage",
            name="Support Triage",
            description="Triage incoming support emails and create tickets",
            workflow_type=WorkflowType.SUPPORT_TRIAGE,
            default_config={
                "auto_reply": False,
                "escalate_after_hours": 24,
                "priority_mapping": {
                    "urgent": ["bug", "outage"],
                    "high": ["feature request", "question"],
                    "low": ["feedback"],
                },
            },
            created_at=datetime.utcnow(),
        ),
    ]
    
    return WorkflowTemplateListResponse(
        templates=templates,
        total=len(templates),
    )


@router.post("/{workflow_id}/enable", response_model=WorkflowResponse)
async def enable_workflow(
    workflow_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Enable a workflow.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    workflow.is_active = True
    workflow.status = WorkflowStatus.ACTIVE
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"Enabled workflow: {workflow.id}")
    
    return WorkflowResponse.from_orm(workflow)


@router.post("/{workflow_id}/disable", response_model=WorkflowResponse)
async def disable_workflow(
    workflow_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Disable a workflow.
    """
    tenant_id = "test-tenant-id"  # Replace with real tenant ID from auth
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    workflow.is_active = False
    workflow.status = WorkflowStatus.INACTIVE
    workflow.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workflow)
    
    logger.info(f"Disabled workflow: {workflow.id}")
    
    return WorkflowResponse.from_orm(workflow)
