"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-14

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("custom_domain", sa.String(255), nullable=True),
        sa.Column("subscription_plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("subscription_status", sa.String(50), nullable=False, server_default="trial"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settings", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_tenant_name", "tenants", ["name"], unique=True)
    op.create_index("ix_tenant_domain", "tenants", ["domain"], unique=True)
    op.create_index("ix_tenant_active", "tenants", ["is_active"])

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("clerk_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("preferences", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_user_email", "users", ["email"], unique=True)
    op.create_index("ix_user_tenant", "users", ["tenant_id"])
    op.create_index("ix_user_clerk", "users", ["clerk_id"], unique=True)
    op.create_index("ix_user_active", "users", ["is_active"])

    # connections
    op.create_table(
        "connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_user_id", sa.String(255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(50), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(20), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_connection_tenant", "connections", ["tenant_id"])
    op.create_index("ix_connection_user", "connections", ["user_id"])
    op.create_index("ix_connection_provider", "connections", ["provider"])
    op.create_index("ix_connection_active", "connections", ["is_active"])
    op.create_index("ix_connection_expires", "connections", ["expires_at"])

    # workflows
    op.create_table(
        "workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "workflow_type",
            sa.Enum(
                "post_meeting_followup",
                "lead_assignment",
                "support_triage",
                "approval_workflow",
                "weekly_summary",
                "custom",
                name="workflow_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "active",
                "inactive",
                "archived",
                name="workflow_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("trigger_config", sa.JSON(), nullable=True),
        sa.Column("template_id", sa.String(36), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_workflow_tenant", "workflows", ["tenant_id"])
    op.create_index("ix_workflow_type", "workflows", ["workflow_type"])
    op.create_index("ix_workflow_status", "workflows", ["status"])
    op.create_index("ix_workflow_active", "workflows", ["is_active"])
    op.create_index("ix_workflow_priority", "workflows", ["priority"])

    # workflow_runs
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflows.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "trigger_type",
            sa.Enum(
                "manual",
                "calendar_event_ended",
                "calendar_event_started",
                "email_received",
                "email_sent",
                "crm_event",
                "webhook",
                "scheduled",
                "api_call",
                name="workflow_run_trigger_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("trigger_data", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "running",
                "completed",
                "failed",
                "cancelled",
                "timeout",
                name="workflow_run_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_stack_trace", sa.Text(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("parent_run_id", sa.String(36), sa.ForeignKey("workflow_runs.id"), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_workflow_run_tenant", "workflow_runs", ["tenant_id"])
    op.create_index("ix_workflow_run_user", "workflow_runs", ["user_id"])
    op.create_index("ix_workflow_run_workflow", "workflow_runs", ["workflow_id"])
    op.create_index("ix_workflow_run_status", "workflow_runs", ["status"])
    op.create_index("ix_workflow_run_trigger", "workflow_runs", ["trigger_type"])
    op.create_index(
        "ix_workflow_run_idempotency", "workflow_runs", ["idempotency_key"], unique=True
    )
    op.create_index("ix_workflow_run_created", "workflow_runs", ["created_at"])
    op.create_index("ix_workflow_run_scheduled", "workflow_runs", ["scheduled_for"])

    # workflow_steps
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "step_type",
            sa.Enum(
                "trigger",
                "llm",
                "tool",
                "parallel",
                "branch",
                "conditional",
                "wait",
                "loop",
                name="workflow_step_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("step_name", sa.String(255), nullable=True),
        sa.Column("tool_name", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                "skipped",
                "timeout",
                name="workflow_step_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_stack_trace", sa.Text(), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("input_data", sa.JSON(), nullable=True),
        sa.Column("output_data", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="30000"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_workflow_step_run", "workflow_steps", ["run_id"])
    op.create_index("ix_workflow_step_type", "workflow_steps", ["step_type"])
    op.create_index("ix_workflow_step_status", "workflow_steps", ["status"])
    op.create_index("ix_workflow_step_order", "workflow_steps", ["order"])
    op.create_index("ix_workflow_step_tool", "workflow_steps", ["tool_name"])
    op.create_index("ix_workflow_step_created", "workflow_steps", ["created_at"])

    # artifacts
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "artifact_type",
            sa.Enum(
                "crm_note",
                "crm_task",
                "crm_deal",
                "crm_contact",
                "crm_company",
                "email_draft",
                "email_sent",
                "document",
                "file",
                "summary",
                "report",
                "log",
                "other",
                name="artifact_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "created",
                "pending",
                "completed",
                "failed",
                "deleted",
                name="artifact_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("content_summary", sa.Text(), nullable=True),
        sa.Column("content_data", sa.JSON(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "parent_artifact_id", sa.String(36), sa.ForeignKey("artifacts.id"), nullable=True
        ),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_artifact_run", "artifacts", ["run_id"])
    op.create_index("ix_artifact_type", "artifacts", ["artifact_type"])
    op.create_index("ix_artifact_external_id", "artifacts", ["external_id"])
    op.create_index("ix_artifact_status", "artifacts", ["status"])
    op.create_index("ix_artifact_created", "artifacts", ["created_at"])


def downgrade():
    op.drop_table("artifacts")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_runs")
    op.drop_table("workflows")
    op.drop_table("connections")
    op.drop_table("users")
    op.drop_table("tenants")
    # Drop enum types (Postgres only — no-op on SQLite).
    for enum_name in [
        "artifact_status_enum",
        "artifact_type_enum",
        "workflow_step_status_enum",
        "workflow_step_type_enum",
        "workflow_run_status_enum",
        "workflow_run_trigger_type_enum",
        "workflow_status_enum",
        "workflow_type_enum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
