"""
Verxlite Worker package.

The actual Celery tasks live in `tasks.py` (kept flat for `celery -A tasks worker`).
This module simply re-exports them so they can be imported as `verxlite_worker.*`
if desired.
"""

from tasks import app, execute_workflow_run, sync_google_calendar, sync_hubspot_contacts, process_webhook_event

__all__ = [
    "app",
    "execute_workflow_run",
    "sync_google_calendar",
    "sync_hubspot_contacts",
    "process_webhook_event",
]
