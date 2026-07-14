"""
Workflows Routes
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from verxlite_api.db.session import get_db
from verxlite_api.deps import get_current_user
from verxlite_api.models.artifact import Artifact
from verxlite_api.models.user import User
from verxlite_api.models.workflow import Workflow, WorkflowStatus, WorkflowType
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus, WorkflowRunTriggerType
from verxlite_api.models.workflow_step import WorkflowStep, WorkflowStepStatus, WorkflowStepType
from verxlite_api.schemas.workflow import (
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowUpdate,
)
from verxlite_api.schemas.workflow_run import (
    WorkflowRunCreate,
    WorkflowRunDetailResponse,
    WorkflowRunListResponse,
    WorkflowRunResponse,
    WorkflowRunStatsResponse,
)
from verxlite_api.utils.logger import get_logger

router = APIRouter(tags=["workflows"])
logger = get_logger("workflows")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


# --------------------------------------------------------------------------- #
# Templates — declared BEFORE /{workflow_id} so the dynamic route doesn't eat them.
# --------------------------------------------------------------------------- #
@router.get("/templates", response_model=WorkflowTemplateListResponse)
async def list_workflow_templates(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """List available workflow templates."""
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
            created_at=datetime.now(timezone.utc),
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
            created_at=datetime.now(timezone.utc),
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
            created_at=datetime.now(timezone.utc),
        ),
    ]
    return WorkflowTemplateListResponse(templates=templates, total=len(templates))


# --------------------------------------------------------------------------- #
# Stats — also before /{workflow_id}.
# --------------------------------------------------------------------------- #
@router.get("/stats", response_model=WorkflowRunStatsResponse)
async def get_workflow_stats(
    request: Request,
    workflow_id: str | None = Query(None, description="Filter by workflow ID"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workflow run statistics for the current tenant."""
    query = db.query(WorkflowRun).filter(WorkflowRun.tenant_id == current_user.tenant_id)

    if workflow_id:
        query = query.filter(WorkflowRun.workflow_id == workflow_id)
    if start_date:
        query = query.filter(WorkflowRun.created_at >= start_date)
    if end_date:
        query = query.filter(WorkflowRun.created_at <= end_date)

    workflow_runs = query.all()

    total_runs = len(workflow_runs)
    successful_runs = sum(1 for r in workflow_runs if r.status == WorkflowRunStatus.COMPLETED)
    failed_runs = sum(1 for r in workflow_runs if r.status == WorkflowRunStatus.FAILED)
    success_rate = successful_runs / total_runs if total_runs > 0 else 0.0
    total_tokens = sum(r.total_tokens for r in workflow_runs)

    durations = [r.total_duration_ms for r in workflow_runs if r.total_duration_ms > 0]
    avg_duration_ms = sum(durations) / len(durations) if durations else 0.0
    if durations:
        sorted_durations = sorted(durations)
        p50 = sorted_durations[len(sorted_durations) // 2]
        p90 = sorted_durations[min(int(len(sorted_durations) * 0.9), len(sorted_durations) - 1)]
    else:
        p50 = 0.0
        p90 = 0.0

    runs_by_workflow: dict = {}
    runs_by_status: dict = {}
    runs_by_trigger: dict = {}
    for r in workflow_runs:
        wf_id = r.workflow_id or "unknown"
        runs_by_workflow[wf_id] = runs_by_workflow.get(wf_id, 0) + 1
        runs_by_status[r.status.value] = runs_by_status.get(r.status.value, 0) + 1
        runs_by_trigger[r.trigger_type.value] = runs_by_trigger.get(r.trigger_type.value, 0) + 1

    return WorkflowRunStatsResponse(
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        success_rate=success_rate,
        total_tokens=total_tokens,
        avg_duration_ms=avg_duration_ms,
        p50_duration_ms=p50,
        p90_duration_ms=p90,
        runs_by_workflow=runs_by_workflow,
        runs_by_status=runs_by_status,
        runs_by_trigger=runs_by_trigger,
    )


# --------------------------------------------------------------------------- #
# Workflow runs list — also before /{workflow_id}.
# --------------------------------------------------------------------------- #
@router.get("/runs", response_model=WorkflowRunListResponse)
async def list_workflow_runs(
    request: Request,
    pagination: PaginationParams = Depends(),
    workflow_id: str | None = Query(None),
    status: WorkflowRunStatus | None = Query(None),
    trigger_type: WorkflowRunTriggerType | None = Query(None),
    search: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workflow runs for the current tenant."""
    query = db.query(WorkflowRun).filter(WorkflowRun.tenant_id == current_user.tenant_id)

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

    total = query.count()
    workflow_runs = (
        query.order_by(WorkflowRun.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    return WorkflowRunListResponse(
        runs=[WorkflowRunResponse.model_validate(r) for r in workflow_runs],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/runs/{run_id}", response_model=WorkflowRunDetailResponse)
async def get_workflow_run(
    run_id: str,
    request: Request,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a workflow run including steps and artifacts."""
    workflow_run = (
        db.query(WorkflowRun)
        .filter(
            WorkflowRun.id == run_id,
            WorkflowRun.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run not found: {run_id}",
        )

    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.run_id == run_id)
        .order_by(WorkflowStep.order.asc())
        .all()
    )
    artifacts = db.query(Artifact).filter(Artifact.run_id == run_id).all()
    workflow = db.query(Workflow).filter(Workflow.id == workflow_run.workflow_id).first()

    return WorkflowRunDetailResponse(
        **WorkflowRunResponse.model_validate(workflow_run).model_dump(),
        steps=[s.to_dict() for s in steps],
        artifacts=[a.to_dict() for a in artifacts],
        workflow=workflow.to_dict() if workflow else None,
    )


# --------------------------------------------------------------------------- #
# Workflow CRUD
# --------------------------------------------------------------------------- #
@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    request: Request,
    pagination: PaginationParams = Depends(),
    workflow_type: WorkflowType | None = Query(None),
    status: WorkflowStatus | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all workflows for the current tenant."""
    query = db.query(Workflow).filter(Workflow.tenant_id == current_user.tenant_id)

    if workflow_type:
        query = query.filter(Workflow.workflow_type == workflow_type)
    if status:
        query = query.filter(Workflow.status == status)
    if is_active is not None:
        query = query.filter(Workflow.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        query = query.filter((Workflow.name.ilike(pattern)) | (Workflow.description.ilike(pattern)))

    total = query.count()
    workflows = (
        query.order_by(Workflow.priority.desc(), Workflow.name.asc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(wf) for wf in workflows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workflow."""
    existing = (
        db.query(Workflow)
        .filter(
            Workflow.tenant_id == current_user.tenant_id,
            Workflow.name == workflow_data.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow with name '{workflow_data.name}' already exists",
        )

    workflow = Workflow(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
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
    logger.info(f"Created workflow: {workflow.id} (tenant={current_user.tenant_id})")
    return WorkflowResponse.model_validate(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific workflow by ID."""
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a workflow."""
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )

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

    db.commit()
    db.refresh(workflow)
    return WorkflowResponse.model_validate(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a workflow (archive)."""
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )

    workflow.is_active = False
    workflow.status = WorkflowStatus.ARCHIVED
    db.commit()
    return None


@router.post(
    "/{workflow_id}/runs", response_model=WorkflowRunResponse, status_code=status.HTTP_201_CREATED
)
async def trigger_workflow_run(
    workflow_id: str,
    run_data: WorkflowRunCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a workflow run.

    In production, this creates a PENDING run and enqueues a Celery task.
    In dev/test (when Celery isn't reachable), the task is run synchronously.
    """
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
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

    # Idempotency check
    idempotency_key = (
        run_data.idempotency_key or f"{workflow_id}:{run_data.trigger_type.value}:{uuid.uuid4()}"
    )
    existing_run = (
        db.query(WorkflowRun)
        .filter(
            WorkflowRun.idempotency_key == idempotency_key,
            WorkflowRun.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if existing_run:
        logger.info(f"Duplicate run detected for idempotency key: {idempotency_key}")
        return WorkflowRunResponse.model_validate(existing_run)

    run_id = str(uuid.uuid4())
    workflow_run = WorkflowRun(
        id=run_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        workflow_id=workflow_id,
        trigger_type=run_data.trigger_type,
        trigger_data=run_data.trigger_data or {},
        status=WorkflowRunStatus.PENDING,
        idempotency_key=idempotency_key,
        scheduled_for=run_data.scheduled_for,
    )
    db.add(workflow_run)

    # Initial trigger step
    step = WorkflowStep(
        run_id=run_id,
        step_type=WorkflowStepType.TRIGGER,
        step_name="Workflow triggered",
        status=WorkflowStepStatus.COMPLETED,
        order=0,
        latency_ms=0,
        tokens_used=0,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(step)
    db.commit()
    db.refresh(workflow_run)

    # Try to enqueue the Celery task; fall back to synchronous execution in dev.
    try:
        from worker.tasks import execute_workflow_run  # type: ignore[import]

        execute_workflow_run.delay(
            run_id=run_id,
            workflow_id=workflow_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            trigger_type=run_data.trigger_type.value,
            trigger_data=run_data.trigger_data or {},
        )
        workflow_run.status = WorkflowRunStatus.QUEUED
        db.commit()
        db.refresh(workflow_run)
    except Exception as e:
        # Dev mode: run synchronously so the system is usable without Redis/Celery.
        logger.warning(f"Celery unavailable ({e}); running workflow synchronously")
        try:
            from verxlite_api.services.workflow_engine import WorkflowEngine

            engine = WorkflowEngine(db)
            engine.execute_workflow(
                workflow_id=workflow_id,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                trigger_type=run_data.trigger_type.value,
                trigger_data=run_data.trigger_data or {},
                run_id=run_id,
            )
            db.refresh(workflow_run)
        except Exception as exec_err:
            logger.error(f"Synchronous workflow execution failed: {exec_err}")
            workflow_run.status = WorkflowRunStatus.FAILED
            workflow_run.error_message = str(exec_err)
            db.commit()
            db.refresh(workflow_run)

    return WorkflowRunResponse.model_validate(workflow_run)


@router.post("/{workflow_id}/enable", response_model=WorkflowResponse)
async def enable_workflow(
    workflow_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable a workflow."""
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow not found: {workflow_id}"
        )
    workflow.is_active = True
    workflow.status = WorkflowStatus.ACTIVE
    db.commit()
    db.refresh(workflow)
    return WorkflowResponse.model_validate(workflow)


@router.post("/{workflow_id}/disable", response_model=WorkflowResponse)
async def disable_workflow(
    workflow_id: str,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disable a workflow."""
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow not found: {workflow_id}"
        )
    workflow.is_active = False
    workflow.status = WorkflowStatus.INACTIVE
    db.commit()
    db.refresh(workflow)
    return WorkflowResponse.model_validate(workflow)
