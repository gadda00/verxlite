"""
Workflow Engine Service

Executes workflows step-by-step. Steps are dynamically defined per workflow type.
The engine accepts an optional `run_id` so the API can pre-create a run and the
worker can execute the same run (instead of each generating its own).
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from verxlite_api.models.artifact import Artifact, ArtifactStatus, ArtifactType
from verxlite_api.models.workflow import Workflow, WorkflowType
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus
from verxlite_api.models.workflow_step import (
    WorkflowStep,
    WorkflowStepStatus,
    WorkflowStepType,
)
from verxlite_api.utils.logger import get_logger

logger = get_logger("workflow_engine")


class WorkflowStepResult:
    """Result of a workflow step execution."""

    def __init__(
        self,
        step_id: str,
        step_type: str,
        step_name: str,
        status: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        latency_ms: int = 0,
        tokens_used: int = 0,
    ):
        self.step_id = step_id
        self.step_type = step_type
        self.step_name = step_name
        self.status = status
        self.input_data = input_data
        self.output_data = output_data
        self.error_message = error_message
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used


class WorkflowEngine:
    """Executes workflows with steps (LLM, tool, parallel, branch)."""

    def __init__(self, db: Session | None = None):
        # Use injected session if provided (preferred — easier to test & scope).
        if db is None:
            from verxlite_api.db.session import session as _session

            db = _session()
        self.db = db

    def execute_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        user_id: str,
        trigger_type: str,
        trigger_data: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> WorkflowRun:
        """Execute a workflow. If `run_id` is provided, update that run; else create a new one."""
        logger.info(f"Executing workflow: {workflow_id} (run_id={run_id})")

        # Get workflow
        workflow = (
            self.db.query(Workflow)
            .filter(
                Workflow.id == workflow_id,
                Workflow.tenant_id == tenant_id,
            )
            .first()
        )
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        trigger_data = trigger_data or {}

        # Either reuse the existing run (created by the API) or create a new one.
        if run_id:
            workflow_run = self.db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
            if not workflow_run:
                raise ValueError(f"WorkflowRun not found: {run_id}")
        else:
            run_id = str(uuid.uuid4())
            idempotency_key = f"{workflow_id}:{trigger_type}:{run_id}"
            workflow_run = WorkflowRun(
                id=run_id,
                tenant_id=tenant_id,
                user_id=user_id,
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                trigger_data=trigger_data,
                status=WorkflowRunStatus.RUNNING,
                idempotency_key=idempotency_key,
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(workflow_run)
            self.db.commit()
            self.db.refresh(workflow_run)

        # Mark as RUNNING (in case the API left it PENDING/QUEUED).
        workflow_run.status = WorkflowRunStatus.RUNNING
        workflow_run.started_at = workflow_run.started_at or datetime.now(timezone.utc)
        self.db.commit()

        # Define steps based on workflow type
        try:
            if workflow.workflow_type == WorkflowType.POST_MEETING_FOLLOWUP:
                steps = self._get_post_meeting_followup_steps(workflow_run, trigger_data)
            elif workflow.workflow_type == WorkflowType.LEAD_ASSIGNMENT:
                steps = self._get_lead_assignment_steps(workflow_run, trigger_data)
            elif workflow.workflow_type == WorkflowType.SUPPORT_TRIAGE:
                steps = self._get_support_triage_steps(workflow_run, trigger_data)
            elif workflow.workflow_type == WorkflowType.WEEKLY_SUMMARY:
                steps = self._get_weekly_summary_steps(workflow_run, trigger_data)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow.workflow_type}")

            # Execute each step, threading outputs into the next step's inputs.
            context: dict[str, Any] = {"trigger_data": trigger_data}
            total_tokens = 0
            start_time = time.time()

            for order, step_def in enumerate(steps, start=1):
                step_result = self._execute_step(workflow_run, step_def, order, context)
                total_tokens += step_result.tokens_used

                # Save the output under the step's "save_as" key for later steps to use.
                save_as = step_def.get("save_as")
                if save_as and step_result.output_data is not None:
                    context[save_as] = step_result.output_data

                if step_result.status == "failed":
                    workflow_run.status = WorkflowRunStatus.FAILED
                    workflow_run.error_message = step_result.error_message
                    workflow_run.completed_at = datetime.now(timezone.utc)
                    workflow_run.total_duration_ms = int((time.time() - start_time) * 1000)
                    workflow_run.total_tokens = total_tokens
                    self.db.commit()
                    self.db.refresh(workflow_run)
                    return workflow_run

            # All steps succeeded
            workflow_run.status = WorkflowRunStatus.COMPLETED
            workflow_run.completed_at = datetime.now(timezone.utc)
            workflow_run.total_duration_ms = int((time.time() - start_time) * 1000)
            workflow_run.total_tokens = total_tokens
            self.db.commit()
            self.db.refresh(workflow_run)
            logger.info(f"Workflow completed: {run_id}")

        except Exception as e:
            logger.error(f"Workflow failed: {run_id}, error: {e}", exc_info=True)
            workflow_run.status = WorkflowRunStatus.FAILED
            workflow_run.error_message = str(e)
            workflow_run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(workflow_run)
            raise

        return workflow_run

    # ------------------------------------------------------------------ #
    # Step definitions per workflow type.
    # ------------------------------------------------------------------ #
    def _get_post_meeting_followup_steps(
        self, workflow_run: WorkflowRun, trigger_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        event_id = trigger_data.get("event_id")
        return [
            {
                "step_type": "tool",
                "step_name": "Fetch calendar event",
                "tool_name": "get_calendar_event",
                "input": {"event_id": event_id},
                "save_as": "calendar_event",
            },
            {
                "step_type": "tool",
                "step_name": "Fetch CRM contact",
                "tool_name": "get_crm_contact",
                "input_from": {"email": "calendar_event.attendees.0.email"},
                "save_as": "crm_contact",
            },
            {
                "step_type": "llm",
                "step_name": "Analyze meeting context",
                "prompt": "Analyze this meeting context and output JSON with summary, action_items, next_steps, and sentiment.",
                "input_keys": ["calendar_event", "crm_contact"],
                "save_as": "llm_analysis",
            },
            {
                "step_type": "tool",
                "step_name": "Create CRM note",
                "tool_name": "create_crm_note",
                "input_from": {
                    "contact_id": "crm_contact.id",
                    "body": "llm_analysis.summary",
                },
                "save_as": "crm_note",
            },
            {
                "step_type": "tool",
                "step_name": "Draft follow-up email",
                "tool_name": "draft_email",
                "input_from": {
                    "to": "calendar_event.attendees.0.email",
                    "subject": "llm_analysis.summary",
                    "body": "llm_analysis.summary",
                },
                "save_as": "email_draft",
            },
            {
                "step_type": "tool",
                "step_name": "Create CRM task",
                "tool_name": "create_crm_task",
                "input_from": {
                    "contact_id": "crm_contact.id",
                    "title": "llm_analysis.action_items.0",
                },
                "save_as": "crm_task",
            },
        ]

    def _get_lead_assignment_steps(
        self, workflow_run: WorkflowRun, trigger_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        return [
            {
                "step_type": "llm",
                "step_name": "Score lead",
                "prompt": "Score this lead (0-100) and recommend an owner.",
                "input_keys": ["trigger_data"],
                "save_as": "lead_score",
            },
            {
                "step_type": "tool",
                "step_name": "Assign owner",
                "tool_name": "assign_lead_owner",
                "input_from": {"lead_id": "trigger_data.lead_id", "score": "lead_score.score"},
                "save_as": "assignment",
            },
        ]

    def _get_support_triage_steps(
        self, workflow_run: WorkflowRun, trigger_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        return [
            {
                "step_type": "llm",
                "step_name": "Classify ticket",
                "prompt": "Classify this support ticket into urgent/high/low and suggest a reply.",
                "input_keys": ["trigger_data"],
                "save_as": "classification",
            },
        ]

    def _get_weekly_summary_steps(
        self, workflow_run: WorkflowRun, trigger_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        return [
            {
                "step_type": "llm",
                "step_name": "Compile summary",
                "prompt": "Compile a weekly summary from deals, tasks, and emails.",
                "input_keys": ["trigger_data"],
                "save_as": "summary",
            },
        ]

    # ------------------------------------------------------------------ #
    # Step execution.
    # ------------------------------------------------------------------ #
    def _resolve_input(self, step_def: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Build the input dict for a step.

        - `input`: literal values (may include None placeholders).
        - `input_from`: dotted paths into the context, e.g. "calendar_event.attendees.0.email".
        """
        resolved: dict[str, Any] = {}
        for k, v in (step_def.get("input") or {}).items():
            resolved[k] = v
        for k, path in (step_def.get("input_from") or {}).items():
            resolved[k] = self._lookup(context, path)
        return resolved

    @staticmethod
    def _lookup(context: dict[str, Any], path: str) -> Any:
        """Resolve a dotted path like 'calendar_event.attendees.0.email' against the context."""
        current: Any = context
        for part in path.split("."):
            if current is None:
                return None
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                try:
                    current = getattr(current, part)
                except AttributeError:
                    return None
        return current

    def _execute_step(
        self,
        workflow_run: WorkflowRun,
        step_def: dict[str, Any],
        order: int,
        context: dict[str, Any],
    ) -> WorkflowStepResult:
        step_id = str(uuid.uuid4())
        step_type = step_def.get("step_type", "tool")
        step_name = step_def.get("step_name", step_type)

        step = WorkflowStep(
            id=step_id,
            run_id=workflow_run.id,
            step_type=(
                WorkflowStepType(step_type)
                if step_type in [t.value for t in WorkflowStepType]
                else WorkflowStepType.TOOL
            ),
            step_name=step_name,
            tool_name=step_def.get("tool_name"),
            status=WorkflowStepStatus.RUNNING,
            order=order,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)

        start_time = time.time()
        try:
            if step_type == "tool":
                result = self._execute_tool_step(step_def, context)
            elif step_type == "llm":
                result = self._execute_llm_step(step_def, context)
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            step.status = (
                WorkflowStepStatus.COMPLETED
                if result.status == "completed"
                else WorkflowStepStatus.FAILED
            )
            step.input_summary = str(result.input_data)[:500] if result.input_data else None
            step.output_summary = str(result.output_data)[:500] if result.output_data else None
            step.error_message = result.error_message
            step.latency_ms = result.latency_ms
            step.tokens_used = result.tokens_used
            step.input_data = result.input_data
            step.output_data = result.output_data
            step.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(step)
            return result

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            step.status = WorkflowStepStatus.FAILED
            step.error_message = str(e)
            step.latency_ms = latency_ms
            step.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return WorkflowStepResult(
                step_id=step_id,
                step_type=step_type,
                step_name=step_name,
                status="failed",
                error_message=str(e),
                latency_ms=latency_ms,
            )

    def _execute_tool_step(
        self, step_def: dict[str, Any], context: dict[str, Any]
    ) -> WorkflowStepResult:
        tool_name = step_def.get("tool_name")
        input_data = self._resolve_input(step_def, context)
        start_time = time.time()

        try:
            # In dev / tests we ship a mock dispatcher so workflows run end-to-end
            # without external API credentials. In production, the worker injects
            # real connectors (GoogleConnector / HubSpotConnector) by overriding
            # `tool_name` dispatch — see `worker/tasks.py`.
            output = self._dispatch_mock_tool(tool_name, input_data)
            latency_ms = int((time.time() - start_time) * 1000)

            # Persist an artifact for some tool outputs.
            self._maybe_persist_artifact(tool_name, output, context)

            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="tool",
                step_name=step_def.get("step_name", tool_name),
                status="completed",
                input_data=input_data,
                output_data=output,
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="tool",
                step_name=step_def.get("step_name", tool_name),
                status="failed",
                input_data=input_data,
                error_message=str(e),
                latency_ms=latency_ms,
            )

    def _execute_llm_step(
        self, step_def: dict[str, Any], context: dict[str, Any]
    ) -> WorkflowStepResult:
        prompt = step_def.get("prompt", "")
        input_keys = step_def.get("input_keys", [])
        # Build the LLM input from the context.
        input_data = {
            "prompt": prompt,
            "inputs": {k: context.get(k) for k in input_keys},
        }
        start_time = time.time()

        try:
            # Try real LLM first; fall back to deterministic mock output.
            output, tokens = self._call_llm(prompt, input_data)
            latency_ms = int((time.time() - start_time) * 1000)
            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="llm",
                step_name=step_def.get("step_name", "LLM"),
                status="completed",
                input_data=input_data,
                output_data=output,
                latency_ms=latency_ms,
                tokens_used=tokens,
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="llm",
                step_name=step_def.get("step_name", "LLM"),
                status="failed",
                input_data=input_data,
                error_message=str(e),
                latency_ms=latency_ms,
            )

    # ------------------------------------------------------------------ #
    # Mock tool dispatcher (dev fallback).
    # ------------------------------------------------------------------ #
    @staticmethod
    def _dispatch_mock_tool(tool_name: str, input_data: dict[str, Any]) -> dict[str, Any]:
        """Produce deterministic mock output for a tool call.

        Real dispatch to Google/HubSpot happens in the worker via dependency
        injection (the API doesn't have access to user OAuth tokens at the
        engine layer without an explicit connection lookup).
        """
        event_id = input_data.get("event_id")
        email = input_data.get("email")
        contact_id = input_data.get("contact_id")
        body = input_data.get("body")
        to = input_data.get("to")
        subject = input_data.get("subject")
        title = input_data.get("title")
        due_date = input_data.get("due_date")

        if tool_name == "get_calendar_event":
            return {
                "id": event_id or "mock_event",
                "summary": "Sales Meeting with Acme Corp",
                "start": "2024-01-01T10:00:00Z",
                "end": "2024-01-01T11:00:00Z",
                "attendees": [
                    {"email": email or "john@acme.com", "name": "John Doe"},
                    {"email": "jane@verxlite.dev", "name": "Jane Smith"},
                ],
            }
        if tool_name == "get_crm_contact":
            return {
                "id": contact_id or "contact_mock",
                "email": email or "john@acme.com",
                "name": "John Doe",
                "company": "Acme Corp",
            }
        if tool_name == "create_crm_note":
            return {"id": f"note_{uuid.uuid4()}", "contact_id": contact_id, "body": body}
        if tool_name == "draft_email":
            return {"id": f"draft_{uuid.uuid4()}", "to": to, "subject": subject, "body": body}
        if tool_name == "create_crm_task":
            return {
                "id": f"task_{uuid.uuid4()}",
                "contact_id": contact_id,
                "title": title,
                "due_date": due_date,
            }
        if tool_name == "assign_lead_owner":
            return {
                "lead_id": input_data.get("lead_id"),
                "owner": "rep_1",
                "score": input_data.get("score", 50),
            }
        raise ValueError(f"Unknown tool: {tool_name}")

    def _maybe_persist_artifact(
        self, tool_name: str, output: dict[str, Any], context: dict[str, Any]
    ) -> None:
        """Persist certain tool outputs as artifacts."""
        run = context.get("_run_id")
        if not run:
            return
        mapping = {
            "create_crm_note": (ArtifactType.CRM_NOTE, output.get("body")),
            "draft_email": (ArtifactType.EMAIL_DRAFT, output.get("body")),
            "create_crm_task": (ArtifactType.CRM_TASK, output.get("title")),
        }
        if tool_name not in mapping:
            return
        art_type, summary = mapping[tool_name]
        artifact = Artifact(
            run_id=run,
            artifact_type=art_type,
            external_id=output.get("id"),
            content_summary=str(summary)[:500] if summary else None,
            content_data=output,
            status=ArtifactStatus.CREATED,
        )
        self.db.add(artifact)
        self.db.commit()

    # ------------------------------------------------------------------ #
    # LLM dispatch (real if configured, mock otherwise).
    # ------------------------------------------------------------------ #
    def _call_llm(self, prompt: str, input_data: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Call the configured LLM provider. Falls back to a deterministic mock."""
        from verxlite_api.config import settings

        # Build a context-aware prompt
        inputs = input_data.get("inputs", {})
        full_prompt = prompt + "\n\nContext:\n" + str(inputs)

        # Try Anthropic
        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic

                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": full_prompt}],
                )
                text = response.content[0].text if response.content else ""
                tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
                # Try to parse JSON; fall back to wrapping in a dict.
                import json

                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed, tokens
                except json.JSONDecodeError:
                    pass
                return {"summary": text, "tokens": tokens}, tokens
            except Exception as e:
                logger.warning(f"Anthropic call failed, falling back to mock: {e}")

        # Try OpenAI
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": full_prompt}],
                )
                text = response.choices[0].message.content or ""
                tokens = response.usage.total_tokens if response.usage else 0
                import json

                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed, tokens
                except json.JSONDecodeError:
                    pass
                return {"summary": text, "tokens": tokens}, tokens
            except Exception as e:
                logger.warning(f"OpenAI call failed, falling back to mock: {e}")

        # Mock: deterministic, useful for tests and dev.
        time.sleep(0.01)
        return {
            "summary": "Discussed Q4 sales targets and next steps for the Acme Corp deal.",
            "action_items": ["Send proposal by Friday", "Schedule follow-up meeting"],
            "next_steps": ["Finalize contract terms", "Get approval from legal"],
            "sentiment": "positive",
            "deal_stage": "proposal",
        }, 1000
