"""
Workflows Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from verxlite_api.config import settings
from verxlite_api.db.session import get_db
from verxlite_api.models.workflow import Workflow
from verxlite_api.models.workflow_run import WorkflowRun
from verxlite_api.models.workflow_step import WorkflowStep
from verxlite_api.models.artifact import Artifact
from verxlite_api.models.connection import Connection
from verxlite_api.utils.logger import get_logger

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = get_logger("workflows")


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    workflow_type: str
    is_active: bool
    created_at: datetime


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]


class WorkflowRunRequest(BaseModel):
    workflow_id: str
    trigger_type: str = "manual"
    trigger_data: Optional[dict] = None


class WorkflowRunResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_type: str
    trigger_data: Optional[dict] = None
    total_tokens: int = 0
    total_duration_ms: int = 0
    created_at: datetime


class WorkflowRunDetailResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    trigger_type: str
    trigger_data: Optional[dict] = None
    total_tokens: int = 0
    total_duration_ms: int = 0
    steps: List[dict] = []
    artifacts: List[dict] = []
    created_at: datetime


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    request: Request,
    db=Depends(get_db),
):
    """
    List all workflows for the current tenant.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    tenant_id = "test-tenant-id"
    
    workflows = db.query(Workflow).filter(Workflow.tenant_id == tenant_id).all()
    
    return WorkflowListResponse(
        workflows=[
            WorkflowResponse(
                id=wf.id,
                name=wf.name,
                description=wf.description,
                workflow_type=wf.workflow_type,
                is_active=wf.is_active,
                created_at=wf.created_at,
            )
            for wf in workflows
        ]
    )


@router.post("/{workflow_id}/runs", response_model=WorkflowRunResponse)
async def trigger_workflow_run(
    workflow_id: str,
    request: WorkflowRunRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
):
    """
    Trigger a workflow run.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    user_id = "test-user-id"
    tenant_id = "test-tenant-id"
    
    # Get workflow
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    # Create workflow run
    run_id = str(uuid.uuid4())
    workflow_run = WorkflowRun(
        id=run_id,
        tenant_id=tenant_id,
        user_id=user_id,
        workflow_id=workflow_id,
        trigger_type=request.trigger_type,
        trigger_data=request.trigger_data,
        status="pending",
        idempotency_key=f"{workflow_id}_{request.trigger_type}_{request.trigger_data.get('event_id', '')}",
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
    
    # In a real implementation, we would:
    # 1. Add the workflow run to a queue (Redis + Celery)
    # 2. The worker would process it in the background
    # For now, we'll just mark it as completed
    workflow_run.status = "completed"
    db.commit()
    
    logger.info(f"Workflow run triggered: {run_id}")
    
    return WorkflowRunResponse(
        id=workflow_run.id,
        workflow_id=workflow_id,
        status=workflow_run.status,
        trigger_type=workflow_run.trigger_type,
        trigger_data=workflow_run.trigger_data,
        total_tokens=workflow_run.total_tokens,
        total_duration_ms=workflow_run.total_duration_ms,
        created_at=workflow_run.created_at,
    )


@router.get("/runs/{run_id}", response_model=WorkflowRunDetailResponse)
async def get_workflow_run(
    run_id: str,
    request: Request,
    db=Depends(get_db),
):
    """
    Get details of a workflow run.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    tenant_id = "test-tenant-id"
    
    workflow_run = db.query(WorkflowRun).filter(
        WorkflowRun.id == run_id,
        WorkflowRun.tenant_id == tenant_id,
    ).first()
    
    if not workflow_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow run not found",
        )
    
    steps = db.query(WorkflowStep).filter(WorkflowStep.run_id == run_id).all()
    artifacts = db.query(Artifact).filter(Artifact.run_id == run_id).all()
    
    return WorkflowRunDetailResponse(
        id=workflow_run.id,
        workflow_id=workflow_run.workflow_id,
        status=workflow_run.status,
        trigger_type=workflow_run.trigger_type,
        trigger_data=workflow_run.trigger_data,
        total_tokens=workflow_run.total_tokens,
        total_duration_ms=workflow_run.total_duration_ms,
        steps=[
            {
                "id": step.id,
                "step_type": step.step_type,
                "step_name": step.step_name,
                "tool_name": step.tool_name,
                "status": step.status,
                "input_summary": step.input_summary,
                "output_summary": step.output_summary,
                "latency_ms": step.latency_ms,
                "tokens_used": step.tokens_used,
                "order": step.order,
                "created_at": step.created_at,
            }
            for step in steps
        ],
        artifacts=[
            {
                "id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "external_id": artifact.external_id,
                "external_url": artifact.external_url,
                "content_summary": artifact.content_summary,
                "created_at": artifact.created_at,
            }
            for artifact in artifacts
        ],
        created_at=workflow_run.created_at,
    )


@router.get("/runs")
async def list_workflow_runs(
    request: Request,
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db=Depends(get_db),
):
    """
    List workflow runs with optional filters.
    """
    # Get current user from JWT
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # For now, we'll use a simple approach - in production, use Clerk
    tenant_id = "test-tenant-id"
    
    query = db.query(WorkflowRun).filter(WorkflowRun.tenant_id == tenant_id)
    
    if workflow_id:
        query = query.filter(WorkflowRun.workflow_id == workflow_id)
    
    if status:
        query = query.filter(WorkflowRun.status == status)
    
    workflow_runs = query.order_by(WorkflowRun.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "runs": [
            {
                "id": run.id,
                "workflow_id": run.workflow_id,
                "status": run.status,
                "trigger_type": run.trigger_type,
                "total_tokens": run.total_tokens,
                "total_duration_ms": run.total_duration_ms,
                "created_at": run.created_at,
            }
            for run in workflow_runs
        ],
        "total": query.count(),
        "limit": limit,
        "offset": offset,
    }
