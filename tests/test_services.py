"""
Tests for Services
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid

from verxlite_api.services.workflow_engine import WorkflowEngine, WorkflowStepResult


class TestWorkflowEngine:
    """Tests for WorkflowEngine service."""
    
    @pytest.fixture
    def workflow_engine(self, db_session):
        """Create a workflow engine with test database."""
        engine = WorkflowEngine()
        engine.db = db_session
        return engine
    
    def test_workflow_step_result_creation(self):
        """Test creating a WorkflowStepResult."""
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
    
    def test_workflow_step_result_failed(self):
        """Test creating a failed WorkflowStepResult."""
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
    def test_execute_workflow(self, mock_db, workflow_engine):
        """Test executing a workflow."""
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
    def test_execute_tool_step(self, mock_db, workflow_engine):
        """Test executing a tool step."""
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
        assert result.latency_ms > 0
    
    @patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
    def test_execute_llm_step(self, mock_db, workflow_engine):
        """Test executing an LLM step."""
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
    
    @patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
    def test_execute_step_tool(self, mock_db, workflow_engine):
        """Test executing a step (tool type)."""
        workflow_run = MagicMock()
        workflow_run.id = "run_1"
        
        step_def = {
            "step_type": "tool",
            "step_name": "Test Tool",
            "tool_name": "test_tool",
            "input": {"key": "value"},
        }
        
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        result = workflow_engine._execute_step(workflow_run, step_def, 0)
        
        assert result.step_type == "tool"
        assert result.status == "completed"
    
    @patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
    def test_execute_step_llm(self, mock_db, workflow_engine):
        """Test executing a step (LLM type)."""
        workflow_run = MagicMock()
        workflow_run.id = "run_1"
        
        step_def = {
            "step_type": "llm",
            "step_name": "Test LLM",
            "prompt": "Test prompt",
            "input_keys": ["key1"],
        }
        
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        result = workflow_engine._execute_step(workflow_run, step_def, 0)
        
        assert result.step_type == "llm"
        assert result.status == "completed"
    
    @patch("verxlite_api.services.workflow_engine.WorkflowEngine.db")
    def test_execute_step_failure(self, mock_db, workflow_engine):
        """Test executing a step that fails."""
        workflow_run = MagicMock()
        workflow_run.id = "run_1"
        
        step_def = {
            "step_type": "tool",
            "step_name": "Failing Tool",
            "tool_name": "failing_tool",
            "input": {"key": "value"},
        }
        
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        # Mock a tool that raises an exception
        with patch.object(workflow_engine, "_execute_tool_step") as mock_tool:
            mock_tool.side_effect = Exception("Tool failed")
            
            result = workflow_engine._execute_step(workflow_run, step_def, 0)
        
        assert result.status == "failed"
        assert result.error_message == "Tool failed"
    
    def test_get_post_meeting_followup_steps(self, workflow_engine):
        """Test getting post-meeting followup steps."""
        workflow_run = MagicMock()
        workflow_run.id = "run_1"
        
        trigger_data = {"event_id": "event_123"}
        
        steps = workflow_engine._get_post_meeting_followup_steps(workflow_run, trigger_data)
        
        assert len(steps) > 0
        assert steps[0]["step_type"] == "tool"
        assert steps[0]["tool_name"] == "get_calendar_event"
