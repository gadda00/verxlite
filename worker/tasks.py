"""
Celery Tasks for Verxlite Worker
"""

from celery import Celery
from celery.utils.log import get_task_logger
import os
import time
import uuid
from datetime import datetime

from verxlite_api.config import settings
from verxlite_api.db.session import session
from verxlite_api.models.workflow_run import WorkflowRun
from verxlite_api.models.workflow_step import WorkflowStep
from verxlite_api.models.artifact import Artifact
from verxlite_api.services.workflow_engine import WorkflowEngine
from verxlite_api.observability.langfuse import LangfuseTracer
from verxlite_api.observability.metrics import MetricsCollector

# Initialize Celery
app = Celery(
    "verxlite_worker",
    broker=settings.REDIS_URL,
    backend="rpc://",
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=300000,  # 300MB
)

logger = get_task_logger(__name__)


@app.task(bind=True, max_retries=3)
def execute_workflow_run(
    self,
    workflow_id: str,
    tenant_id: str,
    user_id: str,
    trigger_type: str,
    trigger_data: dict,
):
    """
    Execute a workflow run in the background.
    """
    logger.info(
        f"Starting workflow run: workflow_id={workflow_id}, tenant_id={tenant_id}, "
        f"trigger_type={trigger_type}"
    )
    
    # Initialize services
    db = session()
    workflow_engine = WorkflowEngine()
    tracer = LangfuseTracer()
    metrics = MetricsCollector()
    
    run_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Execute workflow
        workflow_run = workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            user_id=user_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
        )
        
        # Calculate metrics
        end_time = time.time()
        total_duration_ms = int((end_time - start_time) * 1000)
        
        # Trace workflow run
        tracer.trace_workflow_run(
            run_id=run_id,
            workflow_id=workflow_id,
            workflow_type=workflow_run.workflow.workflow_type,
            tenant_id=tenant_id,
            user_id=user_id,
            status=workflow_run.status,
            total_tokens=workflow_run.total_tokens,
            total_duration_ms=total_duration_ms,
            error_message=workflow_run.error_message,
        )
        
        # Track metrics
        metrics.track_workflow_run(
            workflow_type=workflow_run.workflow.workflow_type,
            status=workflow_run.status,
            duration_ms=total_duration_ms,
            tokens_used=workflow_run.total_tokens,
        )
        
        logger.info(
            f"Completed workflow run: {run_id}, status={workflow_run.status}, "
            f"duration={total_duration_ms}ms, tokens={workflow_run.total_tokens}"
        )
        
        return {
            "status": workflow_run.status,
            "run_id": run_id,
            "workflow_id": workflow_id,
            "total_tokens": workflow_run.total_tokens,
            "total_duration_ms": total_duration_ms,
        }
        
    except Exception as e:
        logger.error(f"Failed workflow run: {run_id}, error: {str(e)}")
        
        # Update workflow run status
        workflow_run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if workflow_run:
            workflow_run.status = "failed"
            workflow_run.error_message = str(e)
            db.commit()
        
        # Trace failure
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
        
        # Retry on certain errors
        if isinstance(e, ConnectionError):
            self.retry(exc=e, countdown=60)
        
        raise


@app.task(bind=True)
def sync_google_calendar(user_id: str, connection_id: str):
    """
    Sync Google Calendar events for a user.
    """
    logger.info(f"Syncing Google Calendar for user: {user_id}")
    
    # In a real implementation, we would:
    # 1. Get the Google connection
    # 2. Fetch recent calendar events
    # 3. Store them in the database
    # 4. Trigger workflows for new events
    
    # For now, we'll just log
    logger.info(f"Synced Google Calendar for user: {user_id}")
    
    return {"status": "ok", "synced_events": 0}


@app.task(bind=True)
def sync_hubspot_contacts(user_id: str, connection_id: str):
    """
    Sync HubSpot contacts for a user.
    """
    logger.info(f"Syncing HubSpot contacts for user: {user_id}")
    
    # In a real implementation, we would:
    # 1. Get the HubSpot connection
    # 2. Fetch recent contacts
    # 3. Store them in the database
    
    # For now, we'll just log
    logger.info(f"Synced HubSpot contacts for user: {user_id}")
    
    return {"status": "ok", "synced_contacts": 0}


@app.task(bind=True)
def process_webhook_event(event_type: str, event_data: dict):
    """
    Process a webhook event (e.g., from Google Calendar).
    """
    logger.info(f"Processing webhook event: {event_type}")
    
    # In a real implementation, we would:
    # 1. Parse the event
    # 2. Find the appropriate workflow
    # 3. Trigger the workflow
    
    # For now, we'll just log
    logger.info(f"Processed webhook event: {event_type}")
    
    return {"status": "ok"}
