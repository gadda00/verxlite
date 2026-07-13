"""
Tests for Workflow Engine
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from verxlite_api.services.workflow_engine import WorkflowEngine, WorkflowStepResult


@pytest.fixture
def workflow_engine():
    return WorkflowEngine()


@pytest.fixture
def mock_db():
    return MagicMock()


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


@patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
def test_execute_workflow(mock_db, workflow_engine):
    """Test workflow execution."""
    # Setup mock database
    mock_workflow = MagicMock()
    mock_workflow.id = "workflow_1"
    mock_workflow.workflow_type = "post_meeting_followup"
    mock_workflow.tenant_id = "tenant_1"
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_workflow
    
    # Execute workflow
    with patch.object(workflow_engine, "_get_post_meeting_followup_steps") as mock_steps:
        mock_steps.return_value = []
        
        result = workflow_engine.execute_workflow(
            workflow_id="workflow_1",
            tenant_id="tenant_1",
            user_id="user_1",
            trigger_type="manual",
            trigger_data={},
        )
    
    assert result is not None
    assert result.workflow_id == "workflow_1"


@patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
def test_execute_tool_step(mock_db, workflow_engine):
    """Test tool step execution."""
    step_def = {
        "step_type": "tool",
        "step_name": "Test Tool",
        "tool_name": "test_tool",
        "input": {"key": "value"},
    }
    
    result = workflow_engine._execute_tool_step(step_def)
    
    assert result.step_type == "tool"
    assert result.step_name == "Test Tool"
    assert result.status == "completed"


@patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
def test_execute_llm_step(mock_db, workflow_engine):
    """Test LLM step execution."""
    step_def = {
        "step_type": "llm",
        "step_name": "Test LLM",
        "prompt": "Test prompt",
        "input_keys": ["key1", "key2"],
    }
    
    result = workflow_engine._execute_llm_step(step_def)
    
    assert result.step_type == "llm"
    assert result.step_name == "Test LLM"
    assert result.status == "completed"
    assert result.tokens_used > 0
