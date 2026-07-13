"""
Workflow Engine Service
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import time

from verxlite_api.db.session import session
from verxlite_api.models.workflow import Workflow
from verxlite_api.models.workflow_run import WorkflowRun
from verxlite_api.models.workflow_step import WorkflowStep
from verxlite_api.models.artifact import Artifact
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
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
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
    """
    Executes workflows with steps (LLM, tool, parallel, branch).
    """
    
    def __init__(self):
        self.db = session()
    
    def execute_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        user_id: str,
        trigger_type: str,
        trigger_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowRun:
        """
        Execute a workflow and return the workflow run.
        """
        logger.info(f"Executing workflow: {workflow_id}")
        
        # Get workflow
        workflow = self.db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.tenant_id == tenant_id,
        ).first()
        
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create workflow run
        run_id = str(uuid.uuid4())
        workflow_run = WorkflowRun(
            id=run_id,
            tenant_id=tenant_id,
            user_id=user_id,
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            trigger_data=trigger_data,
            status="running",
            idempotency_key=f"{workflow_id}_{trigger_type}_{trigger_data.get('event_id', '')}",
        )
        
        self.db.add(workflow_run)
        self.db.commit()
        self.db.refresh(workflow_run)
        
        # Execute steps
        start_time = time.time()
        total_tokens = 0
        
        try:
            # Define workflow steps based on workflow type
            if workflow.workflow_type == "post_meeting_followup":
                steps = self._get_post_meeting_followup_steps(workflow_run, trigger_data)
            else:
                raise ValueError(f"Unknown workflow type: {workflow.workflow_type}")
            
            # Execute each step
            for order, step_def in enumerate(steps):
                step_result = self._execute_step(workflow_run, step_def, order)
                total_tokens += step_result.tokens_used
                
                if step_result.status == "failed":
                    workflow_run.status = "failed"
                    workflow_run.error_message = step_result.error_message
                    self.db.commit()
                    break
            
            # Update workflow run
            end_time = time.time()
            workflow_run.total_duration_ms = int((end_time - start_time) * 1000)
            workflow_run.total_tokens = total_tokens
            
            if workflow_run.status == "running":
                workflow_run.status = "completed"
            
            self.db.commit()
            self.db.refresh(workflow_run)
            
            logger.info(f"Workflow completed: {run_id}")
            
        except Exception as e:
            logger.error(f"Workflow failed: {run_id}, error: {str(e)}")
            workflow_run.status = "failed"
            workflow_run.error_message = str(e)
            self.db.commit()
            raise
        
        return workflow_run
    
    def _get_post_meeting_followup_steps(
        self,
        workflow_run: WorkflowRun,
        trigger_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Define steps for the post-meeting followup workflow.
        """
        event_id = trigger_data.get("event_id") if trigger_data else None
        
        return [
            {
                "step_type": "tool",
                "step_name": "Fetch calendar event",
                "tool_name": "get_calendar_event",
                "input": {"event_id": event_id},
            },
            {
                "step_type": "tool",
                "step_name": "Fetch CRM contact",
                "tool_name": "get_crm_contact",
                "input": {"email": None},  # Will be populated from previous step
            },
            {
                "step_type": "llm",
                "step_name": "Analyze meeting context",
                "prompt": "Analyze this meeting context and output JSON with summary, action_items, next_steps, and sentiment.",
                "input_keys": ["calendar_event", "crm_contact"],
            },
            {
                "step_type": "tool",
                "step_name": "Create CRM note",
                "tool_name": "create_crm_note",
                "input": {"contact_id": None, "body": None},  # Will be populated from LLM
            },
            {
                "step_type": "tool",
                "step_name": "Draft follow-up email",
                "tool_name": "draft_email",
                "input": {"to": None, "subject": None, "body": None},  # Will be populated from LLM
            },
            {
                "step_type": "tool",
                "step_name": "Create CRM task",
                "tool_name": "create_crm_task",
                "input": {"contact_id": None, "title": None, "due_date": None},  # Will be populated from LLM
            },
        ]
    
    def _execute_step(
        self,
        workflow_run: WorkflowRun,
        step_def: Dict[str, Any],
        order: int,
    ) -> WorkflowStepResult:
        """
        Execute a single workflow step.
        """
        step_id = str(uuid.uuid4())
        step_type = step_def.get("step_type")
        step_name = step_def.get("step_name")
        
        # Create step record
        step = WorkflowStep(
            id=step_id,
            run_id=workflow_run.id,
            step_type=step_type,
            step_name=step_name,
            tool_name=step_def.get("tool_name"),
            status="running",
            order=order,
        )
        
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        
        start_time = time.time()
        
        try:
            if step_type == "tool":
                result = self._execute_tool_step(step_def)
                step.status = result.status
                step.input_summary = str(result.input_data)[:500] if result.input_data else None
                step.output_summary = str(result.output_data)[:500] if result.output_data else None
                step.error_message = result.error_message
                step.latency_ms = result.latency_ms
                step.tokens_used = result.tokens_used
                
            elif step_type == "llm":
                result = self._execute_llm_step(step_def)
                step.status = result.status
                step.input_summary = str(result.input_data)[:500] if result.input_data else None
                step.output_summary = str(result.output_data)[:500] if result.output_data else None
                step.error_message = result.error_message
                step.latency_ms = result.latency_ms
                step.tokens_used = result.tokens_used
                
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            self.db.commit()
            self.db.refresh(step)
            
            return result
            
        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.latency_ms = int((time.time() - start_time) * 1000)
            self.db.commit()
            return WorkflowStepResult(
                step_id=step_id,
                step_type=step_type,
                step_name=step_name,
                status="failed",
                error_message=str(e),
                latency_ms=int((time.time() - start_time) * 1000),
            )
    
    def _execute_tool_step(self, step_def: Dict[str, Any]) -> WorkflowStepResult:
        """
        Execute a tool step.
        """
        tool_name = step_def.get("tool_name")
        input_data = step_def.get("input", {})
        
        start_time = time.time()
        
        try:
            # In a real implementation, we would call the actual tool
            # For now, we'll simulate it
            if tool_name == "get_calendar_event":
                event_id = input_data.get("event_id")
                # Simulate fetching calendar event
                time.sleep(0.5)
                output = {
                    "id": event_id,
                    "summary": "Sales Meeting with Acme Corp",
                    "start": "2024-01-01T10:00:00Z",
                    "end": "2024-01-01T11:00:00Z",
                    "attendees": [
                        {"email": "john@acme.com", "name": "John Doe"},
                        {"email": "jane@verxlite.dev", "name": "Jane Smith"},
                    ],
                }
                
            elif tool_name == "get_crm_contact":
                email = input_data.get("email")
                # Simulate fetching CRM contact
                time.sleep(0.5)
                output = {
                    "id": "contact_123",
                    "email": email,
                    "name": "John Doe",
                    "company": "Acme Corp",
                }
                
            elif tool_name == "create_crm_note":
                contact_id = input_data.get("contact_id")
                body = input_data.get("body")
                # Simulate creating CRM note
                time.sleep(0.5)
                output = {
                    "id": f"note_{uuid.uuid4()}",
                    "contact_id": contact_id,
                    "body": body,
                }
                
            elif tool_name == "draft_email":
                to = input_data.get("to")
                subject = input_data.get("subject")
                body = input_data.get("body")
                # Simulate drafting email
                time.sleep(0.5)
                output = {
                    "id": f"draft_{uuid.uuid4()}",
                    "to": to,
                    "subject": subject,
                    "body": body,
                }
                
            elif tool_name == "create_crm_task":
                contact_id = input_data.get("contact_id")
                title = input_data.get("title")
                due_date = input_data.get("due_date")
                # Simulate creating CRM task
                time.sleep(0.5)
                output = {
                    "id": f"task_{uuid.uuid4()}",
                    "contact_id": contact_id,
                    "title": title,
                    "due_date": due_date,
                }
                
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            
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
    
    def _execute_llm_step(self, step_def: Dict[str, Any]) -> WorkflowStepResult:
        """
        Execute an LLM step.
        """
        prompt = step_def.get("prompt")
        input_keys = step_def.get("input_keys", [])
        
        start_time = time.time()
        
        try:
            # In a real implementation, we would call the LLM
            # For now, we'll simulate it
            time.sleep(1)  # Simulate LLM latency
            
            # Simulate LLM output
            output = {
                "summary": "Discussed Q4 sales targets and next steps for the Acme Corp deal.",
                "action_items": [
                    "Send proposal by Friday",
                    "Schedule follow-up meeting",
                ],
                "next_steps": [
                    "Finalize contract terms",
                    "Get approval from legal",
                ],
                "sentiment": "positive",
                "deal_stage": "proposal",
            }
            
            latency_ms = int((time.time() - start_time) * 1000)
            tokens_used = 1000  # Simulate token usage
            
            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="llm",
                step_name=step_def.get("step_name", "LLM"),
                status="completed",
                input_data={"prompt": prompt, "input_keys": input_keys},
                output_data=output,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            return WorkflowStepResult(
                step_id=str(uuid.uuid4()),
                step_type="llm",
                step_name=step_def.get("step_name", "LLM"),
                status="failed",
                input_data={"prompt": prompt, "input_keys": input_keys},
                error_message=str(e),
                latency_ms=latency_ms,
            )
