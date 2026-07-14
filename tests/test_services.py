"""
Tests for Services (WorkflowEngine)
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import uuid

from verxlite_api.services.workflow_engine import WorkflowEngine, WorkflowStepResult
from verxlite_api.models.workflow import Workflow, WorkflowType, WorkflowStatus
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus, WorkflowRunTriggerType


class TestWorkflowStepResult:
    """Tests for WorkflowStepResult."""

    def test_step_result_creation(self):
        result = WorkflowStepResult(
            step_id="step_1",
            step_type="tool",
            step_name="Test Step",
            status="completed",
            input_data={"key": "value"},
            output_data={"result": "success"},
            latency_ms=100,
            tokens_used=50,
        )
        assert result.step_id == "step_1"
        assert result.status == "completed"
        assert result.latency_ms == 100
        assert result.tokens_used == 50

    def test_step_result_failed(self):
        result = WorkflowStepResult(
            step_id="step_2",
            step_type="llm",
            step_name="LLM Step",
            status="failed",
            error_message="LLM error",
            latency_ms=200,
        )
        assert result.status == "failed"
        assert result.error_message == "LLM error"


class TestWorkflowEngine:
    """Tests for WorkflowEngine service."""

    @pytest.fixture
    def workflow_engine(self, db_session):
        return WorkflowEngine(db=db_session)

    def test_execute_workflow_with_real_workflow(
        self,
        workflow_engine,
        db_session,
        test_tenant,
        test_user,
    ):
        """End-to-end: create a real workflow and execute it."""
        workflow = Workflow(
            tenant_id=test_tenant.id,
            created_by=test_user.id,
            name="Engine Test Workflow",
            workflow_type=WorkflowType.POST_MEETING_FOLLOWUP,
            is_active=True,
            status=WorkflowStatus.ACTIVE,
            priority=5,
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)

        run = workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            trigger_type="manual",
            trigger_data={"event_id": "evt_1"},
        )

        assert run is not None
        assert run.workflow_id == workflow.id
        assert run.status == WorkflowRunStatus.COMPLETED
        assert run.total_duration_ms > 0
        # The mock LLM uses 1000 tokens.
        assert run.total_tokens == 1000

    def test_execute_workflow_unknown_type_raises(
        self,
        workflow_engine,
        db_session,
        test_tenant,
        test_user,
    ):
        workflow = Workflow(
            tenant_id=test_tenant.id,
            created_by=test_user.id,
            name="Unknown Type Workflow",
            workflow_type=WorkflowType.CUSTOM,
            is_active=True,
            status=WorkflowStatus.ACTIVE,
            priority=5,
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)

        with pytest.raises(ValueError, match="Unsupported workflow type"):
            workflow_engine.execute_workflow(
                workflow_id=workflow.id,
                tenant_id=test_tenant.id,
                user_id=test_user.id,
                trigger_type="manual",
                trigger_data={},
            )

    def test_execute_workflow_workflow_not_found(self, workflow_engine):
        with pytest.raises(ValueError, match="Workflow not found"):
            workflow_engine.execute_workflow(
                workflow_id="nonexistent",
                tenant_id="any",
                user_id="any",
                trigger_type="manual",
                trigger_data={},
            )

    def test_execute_tool_step_mock(self, workflow_engine):
        """Mock tool step should produce deterministic output."""
        step_def = {
            "step_type": "tool",
            "step_name": "Fetch calendar event",
            "tool_name": "get_calendar_event",
            "input": {"event_id": "evt_42"},
        }
        result = workflow_engine._execute_tool_step(step_def, context={})
        assert result.status == "completed"
        assert result.output_data["id"] == "evt_42"
        assert "attendees" in result.output_data

    def test_execute_tool_step_unknown_tool(self, workflow_engine):
        step_def = {
            "step_type": "tool",
            "step_name": "Bad tool",
            "tool_name": "nonexistent_tool",
            "input": {},
        }
        result = workflow_engine._execute_tool_step(step_def, context={})
        assert result.status == "failed"
        assert "Unknown tool" in (result.error_message or "")

    def test_execute_llm_step_mock(self, workflow_engine):
        step_def = {
            "step_type": "llm",
            "step_name": "Analyze",
            "prompt": "Summarize this meeting.",
            "input_keys": ["calendar_event"],
        }
        result = workflow_engine._execute_llm_step(step_def, context={"calendar_event": {"id": "x"}})
        assert result.status == "completed"
        assert "summary" in result.output_data
        assert result.tokens_used == 1000

    def test_get_post_meeting_followup_steps(self, workflow_engine):
        workflow_run = MagicMock()
        workflow_run.id = "run_1"
        steps = workflow_engine._get_post_meeting_followup_steps(workflow_run, {"event_id": "e1"})
        assert len(steps) == 6
        assert steps[0]["tool_name"] == "get_calendar_event"
        assert steps[0].get("save_as") == "calendar_event"

    def test_lookup_resolves_dotted_path(self, workflow_engine):
        ctx = {"a": {"b": [{"c": 42}]}}
        assert workflow_engine._lookup(ctx, "a.b.0.c") == 42

    def test_lookup_returns_none_on_missing(self, workflow_engine):
        ctx = {"a": {}}
        assert workflow_engine._lookup(ctx, "a.b.c") is None

    def test_step_output_threading(
        self,
        workflow_engine,
        db_session,
        test_tenant,
        test_user,
    ):
        """Step outputs should be saved under `save_as` and accessible to later steps."""
        workflow = Workflow(
            tenant_id=test_tenant.id,
            created_by=test_user.id,
            name="Threading Test",
            workflow_type=WorkflowType.POST_MEETING_FOLLOWUP,
            is_active=True,
            status=WorkflowStatus.ACTIVE,
            priority=5,
        )
        db_session.add(workflow)
        db_session.commit()
        db_session.refresh(workflow)

        run = workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            trigger_type="manual",
            trigger_data={"event_id": "evt_threading"},
        )
        # Steps should be persisted.
        from verxlite_api.models.workflow_step import WorkflowStep
        steps = db_session.query(WorkflowStep).filter(WorkflowStep.run_id == run.id).all()
        # 1 trigger (added by route) + 6 engine steps = 7, but the engine path here
        # didn't add a trigger step, so expect 6.
        assert len(steps) == 6
        # All steps should be COMPLETED
        statuses = {s.status.value for s in steps}
        assert statuses == {"completed"}
