"""
Workflow Model
"""

from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from verxlite_api.db.base import BaseModel


class WorkflowStatus(PyEnum):
    """Status of a workflow."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowType(PyEnum):
    """Type of workflow."""

    POST_MEETING_FOLLOWUP = "post_meeting_followup"
    LEAD_ASSIGNMENT = "lead_assignment"
    SUPPORT_TRIAGE = "support_triage"
    APPROVAL_WORKFLOW = "approval_workflow"
    WEEKLY_SUMMARY = "weekly_summary"
    CUSTOM = "custom"


class Workflow(BaseModel):
    """
    Represents a workflow definition.

    Attributes:
        tenant_id: Tenant this workflow belongs to
        created_by: User who created this workflow
        name: Name of the workflow
        description: Description of what the workflow does
        workflow_type: Type of workflow (from WorkflowType enum)
        config: Workflow-specific configuration (JSON)
        is_active: Whether the workflow is active
        status: Current status of the workflow
        trigger_config: Configuration for workflow triggers
        template_id: ID of the template this workflow was created from
        version: Version of the workflow
        priority: Priority of the workflow (1-10, higher is more important)
    """

    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflow_tenant", "tenant_id"),
        Index("ix_workflow_type", "workflow_type"),
        Index("ix_workflow_status", "status"),
        Index("ix_workflow_active", "is_active"),
        Index("ix_workflow_priority", "priority"),
    )

    tenant_id = Column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(
        Enum(
            WorkflowType,
            name="workflow_type_enum",
            create_type=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=WorkflowType.POST_MEETING_FOLLOWUP,
        nullable=False,
    )
    config = Column(JSON, nullable=True, default=dict)  # Workflow-specific configuration
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(
        Enum(
            WorkflowStatus,
            name="workflow_status_enum",
            create_type=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=WorkflowStatus.ACTIVE,
        nullable=False,
    )
    trigger_config = Column(JSON, nullable=True, default=dict)  # Trigger configuration
    template_id = Column(String(36), nullable=True)  # ID of the template
    version = Column(String(50), default="1.0", nullable=False)  # Version of the workflow
    priority = Column(Integer, default=5, nullable=False)  # Priority (1-10)

    # Relationships
    tenant = relationship("Tenant", backref="workflows")
    # `creator` is created via backref on User.created_workflows.
    runs = relationship("WorkflowRun", backref="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, type={self.workflow_type.value}, status={self.status.value})>"

    def to_dict(self):
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "created_by": self.created_by,
            "name": self.name,
            "description": self.description,
            "workflow_type": self.workflow_type.value,
            "config": self.config,
            "is_active": self.is_active,
            "status": self.status.value,
            "trigger_config": self.trigger_config,
            "template_id": self.template_id,
            "version": self.version,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def get_default_config(cls, workflow_type: WorkflowType) -> dict:
        """Get default configuration for a workflow type."""
        configs = {
            WorkflowType.POST_MEETING_FOLLOWUP: {
                "create_crm_note": True,
                "draft_email": True,
                "create_task": True,
                "email_template": "followup",
                "note_template": "summary",
                "task_due_days": 2,
            },
            WorkflowType.LEAD_ASSIGNMENT: {
                "assign_to": "round_robin",
                "followup_sequence": [1, 3, 7],  # Days
                "notification_enabled": True,
            },
            WorkflowType.SUPPORT_TRIAGE: {
                "auto_reply": False,
                "escalate_after_hours": 24,
                "priority_mapping": {
                    "urgent": ["bug", "outage"],
                    "high": ["feature request", "question"],
                    "low": ["feedback"],
                },
            },
            WorkflowType.APPROVAL_WORKFLOW: {
                "approvers": [],
                "escalation_after_hours": 48,
                "auto_approve_if_no_response": False,
            },
            WorkflowType.WEEKLY_SUMMARY: {
                "include_deals": True,
                "include_tasks": True,
                "include_emails": False,
                "send_day": "monday",
                "send_time": "09:00",
            },
            WorkflowType.CUSTOM: {},
        }
        return configs.get(workflow_type, {})
