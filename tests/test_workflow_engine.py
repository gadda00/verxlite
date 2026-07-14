"""
Tests for the WorkflowEngine (additional coverage beyond test_services.py).
"""

import pytest
from unittest.mock import MagicMock

from verxlite_api.services.workflow_engine import WorkflowEngine, WorkflowStepResult


@pytest.fixture
def workflow_engine(db_session):
    return WorkflowEngine(db=db_session)


def test_workflow_step_result():
    """Test WorkflowStepResult creation."""
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
    assert result.step_type == "tool"
    assert result.step_name == "Test Step"
    assert result.status == "completed"
    assert result.latency_ms == 100
    assert result.tokens_used == 50


def test_workflow_step_result_failed():
    """Test WorkflowStepResult for failed step."""
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


def test_execute_tool_step_returns_completed(workflow_engine):
    """Tool step should complete with deterministic mock output."""
    step_def = {
        "step_type": "tool",
        "step_name": "Test Tool",
        "tool_name": "get_calendar_event",
        "input": {"event_id": "evt_99"},
    }
    result = workflow_engine._execute_tool_step(step_def, context={})
    assert result.step_type == "tool"
    assert result.step_name == "Test Tool"
    assert result.status == "completed"
    assert result.output_data["id"] == "evt_99"


def test_execute_llm_step_returns_completed(workflow_engine):
    """LLM step should complete with the mock summary output."""
    step_def = {
        "step_type": "llm",
        "step_name": "Test LLM",
        "prompt": "Test prompt",
        "input_keys": ["key1", "key2"],
    }
    result = workflow_engine._execute_llm_step(step_def, context={})
    assert result.step_type == "llm"
    assert result.step_name == "Test LLM"
    assert result.status == "completed"
    assert result.tokens_used > 0


def test_resolve_input_merges_input_and_input_from(workflow_engine):
    """`input` and `input_from` should both be resolved into the input dict."""
    step_def = {
        "input": {"event_id": "literal_id"},
        "input_from": {"email": "calendar_event.attendees.0.email"},
    }
    ctx = {"calendar_event": {"attendees": [{"email": "john@acme.com"}]}}
    resolved = workflow_engine._resolve_input(step_def, ctx)
    assert resolved == {"event_id": "literal_id", "email": "john@acme.com"}


def test_dispatch_mock_tool_for_all_known_tools(workflow_engine):
    """Every documented tool should produce an output dict without raising."""
    cases = [
        ("get_calendar_event", {"event_id": "e"}),
        ("get_crm_contact", {"email": "x@y.com"}),
        ("create_crm_note", {"contact_id": "c", "body": "b"}),
        ("draft_email", {"to": "x@y.com", "subject": "s", "body": "b"}),
        ("create_crm_task", {"contact_id": "c", "title": "t"}),
        ("assign_lead_owner", {"lead_id": "l1", "score": 80}),
    ]
    for tool_name, input_data in cases:
        out = workflow_engine._dispatch_mock_tool(tool_name, input_data)
        assert isinstance(out, dict)
        assert "id" in out or "lead_id" in out
