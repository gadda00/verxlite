"""
WorkflowStep Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Integer
from verxlite_api.db.base import BaseModel


class WorkflowStep(BaseModel):
    """
    Represents a single step in a workflow run.
    """
    __tablename__ = "workflow_steps"

    run_id = Column(String(36), ForeignKey("workflow_runs.id"), nullable=False, index=True)
    
    # Step information
    step_type = Column(String(50), nullable=False)  # llm, tool, parallel, branch
    step_name = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=True)  # e.g., get_calendar_event, create_crm_note
    
    # Execution status
    status = Column(String(20), default="pending", nullable=False)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Input/Output (sanitized, no PII)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Performance metrics
    latency_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    
    # Order
    order = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<WorkflowStep(id={self.id}, run_id={self.run_id}, step_type={self.step_type})>"
