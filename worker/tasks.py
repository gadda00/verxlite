"""
Celery Tasks for Verxlite Worker

Wires the API's WorkflowEngine to the Celery queue. The API creates a PENDING
WorkflowRun and enqueues `execute_workflow_run.delay(run_id=...)`. The worker
picks it up and runs the engine against the existing run.
"""

from celery import Celery
from celery.utils.log import get_task_logger
import os
import time
from typing import Any, Optional

# Make sure `verxlite_api` is importable when running from the worker dir.
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus
from verxlite_api.services.workflow_engine import WorkflowEngine
from verxlite_api.observability.langfuse import LangfuseTracer
from verxlite_api.observability.metrics import MetricsCollector

# Initialize Celery
app = Celery(
    "verxlite_worker",
    broker=settings.REDIS_URL,
    backend="rpc://",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=300000,  # 300MB
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_time_limit=600,        # 10 min hard kill
    task_soft_time_limit=540,   # 9 min soft kill
    task_track_started=True,
)

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    max_retries=3,
    autoretry_for=(Exception,),
    retry_backoff=True,         # exponential backoff: 1, 2, 4, 8, ... (×60s by default)
    retry_backoff_max=600,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def execute_workflow_run(
    self,
    run_id: str,
    workflow_id: str,
    tenant_id: str,
    user_id: str,
    trigger_type: str,
    trigger_data: Optional[dict] = None,
) -> dict[str, Any]:
    """Execute a workflow run in the background.

    The run must already exist in the DB (the API creates it PENDING). The
    engine updates it in place.
    """
    trigger_data = trigger_data or {}
    logger.info(
        f"Starting workflow run: run_id={run_id}, workflow_id={workflow_id}, "
        f"tenant_id={tenant_id}, trigger_type={trigger_type}"
    )

    db = session()
    tracer = LangfuseTracer()
    metrics = MetricsCollector()
    start_time = time.time()

    try:
        engine = WorkflowEngine(db)
        workflow_run = engine.execute_workflow(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            run_id=run_id,
        )

        total_duration_ms = int((time.time() - start_time) * 1000)

        # Get workflow type for tracing
        workflow_type = "unknown"
        if workflow_run.workflow:
            workflow_type = workflow_run.workflow.workflow_type.value

        tracer.trace_workflow_run(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            tenant_id=tenant_id,
            user_id=user_id,
            status=workflow_run.status.value,
            total_tokens=workflow_run.total_tokens,
            total_duration_ms=total_duration_ms,
            error_message=workflow_run.error_message,
        )

        metrics.track_workflow_run(
            workflow_type=workflow_type,
            status=workflow_run.status.value,
            duration_ms=total_duration_ms,
            tokens_used=workflow_run.total_tokens,
        )

        logger.info(
            f"Completed workflow run: {run_id}, status={workflow_run.status.value}, "
            f"duration={total_duration_ms}ms, tokens={workflow_run.total_tokens}"
        )

        return {
            "status": workflow_run.status.value,
            "run_id": run_id,
            "workflow_id": workflow_id,
            "total_tokens": workflow_run.total_tokens,
            "total_duration_ms": total_duration_ms,
        }

    except Exception as e:
        logger.error(f"Failed workflow run: {run_id}, error: {e}", exc_info=True)

        # Mark the run as FAILED (the engine may have already done this, but be defensive).
        try:
            wf_run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
            if wf_run and wf_run.status not in [
                WorkflowRunStatus.COMPLETED,
                WorkflowRunStatus.FAILED,
                WorkflowRunStatus.CANCELLED,
            ]:
                wf_run.status = WorkflowRunStatus.FAILED
                wf_run.error_message = str(e)
                db.commit()
        except Exception as cleanup_err:
            logger.error(f"Failed to mark run {run_id} as failed: {cleanup_err}")

        tracer.trace_workflow_run(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_type="unknown",
            tenant_id=tenant_id,
            user_id=user_id,
            status="failed",
            total_tokens=0,
            total_duration_ms=int((time.time() - start_time) * 1000),
            error_message=str(e),
        )

        raise

    finally:
        # ALWAYS close the session to avoid leaks across prefork tasks.
        db.close()
        session.remove()


@app.task(bind=True)
def sync_google_calendar(user_id: str, connection_id: str):
    """Sync Google Calendar events for a user (stub — logs only)."""
    logger.info(f"Syncing Google Calendar for user: {user_id}")
    # TODO: implement real sync via GoogleConnector.list_calendar_events
    return {"status": "ok", "synced_events": 0}


@app.task(bind=True)
def sync_hubspot_contacts(user_id: str, connection_id: str):
    """Sync HubSpot contacts for a user (stub — logs only)."""
    logger.info(f"Syncing HubSpot contacts for user: {user_id}")
    # TODO: implement real sync via HubSpotConnector
    return {"status": "ok", "synced_contacts": 0}


@app.task(bind=True)
def process_webhook_event(event_type: str, event_data: dict):
    """Process a webhook event (stub — logs only)."""
    logger.info(f"Processing webhook event: {event_type}")
    return {"status": "ok"}
