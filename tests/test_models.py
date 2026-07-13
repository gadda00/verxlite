"""
Tests for Database Models
"""

import pytest
from datetime import datetime, timedelta

from verxlite_api.models.tenant import Tenant
from verxlite_api.models.user import User
from verxlite_api.models.connection import Connection
from verxlite_api.models.workflow import Workflow, WorkflowType, WorkflowStatus
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus, WorkflowRunTriggerType
from verxlite_api.models.workflow_step import WorkflowStep, WorkflowStepStatus, WorkflowStepType
from verxlite_api.models.artifact import Artifact, ArtifactType, ArtifactStatus


class TestTenantModel:
    """Tests for Tenant model."""
    
    def test_tenant_creation(self, db_session):
        """Test creating a tenant."""
        tenant = Tenant(
            name="Test Tenant",
            description="Test description",
            domain="test.com",
            is_active=True,
        )
        db_session.add(tenant)
        db_session.commit()
        
        assert tenant.id is not None
        assert tenant.name == "Test Tenant"
        assert tenant.description == "Test description"
        assert tenant.domain == "test.com"
        assert tenant.is_active is True
        assert tenant.created_at is not None
        assert tenant.updated_at is not None
    
    def test_tenant_to_dict(self, test_tenant):
        """Test converting tenant to dictionary."""
        tenant_dict = test_tenant.to_dict()
        
        assert tenant_dict["id"] == test_tenant.id
        assert tenant_dict["name"] == test_tenant.name
        assert tenant_dict["is_active"] == test_tenant.is_active
        assert "created_at" in tenant_dict
        assert "updated_at" in tenant_dict


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self, db_session, test_tenant):
        """Test creating a user."""
        user = User(
            tenant_id=test_tenant.id,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == "admin"
        assert user.is_active is True
    
    def test_user_full_name(self, test_user):
        """Test user full name property."""
        assert test_user.full_name == "Test User"
    
    def test_user_full_name_missing(self, db_session, test_tenant):
        """Test user full name with missing names."""
        user = User(
            tenant_id=test_tenant.id,
            email="test@example.com",
            role="member",
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.full_name == ""
    
    def test_user_to_dict(self, test_user):
        """Test converting user to dictionary."""
        user_dict = test_user.to_dict()
        
        assert user_dict["id"] == test_user.id
        assert user_dict["email"] == test_user.email
        assert user_dict["full_name"] == test_user.full_name
        assert user_dict["role"] == test_user.role


class TestConnectionModel:
    """Tests for Connection model."""
    
    def test_connection_creation(self, db_session, test_tenant, test_user):
        """Test creating a connection."""
        connection = Connection(
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            provider="google",
            provider_user_id="google_user_123",
            access_token="encrypted_token",
            refresh_token="encrypted_refresh",
            token_type="Bearer",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scope="email,profile",
            is_active=True,
        )
        db_session.add(connection)
        db_session.commit()
        
        assert connection.id is not None
        assert connection.provider == "google"
        assert connection.provider_user_id == "google_user_123"
        assert connection.is_active is True
    
    def test_connection_is_expired(self, db_session, test_tenant, test_user):
        """Test connection expiration check."""
        # Expired connection
        expired_conn = Connection(
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            provider="google",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(expired_conn)
        db_session.commit()
        
        assert expired_conn.is_expired is True
        
        # Active connection
        active_conn = Connection(
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            provider="google",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db_session.add(active_conn)
        db_session.commit()
        
        assert active_conn.is_expired is False
    
    def test_connection_scopes(self, test_connection_google):
        """Test connection scopes."""
        assert "email" in test_connection_google.scopes_list
        assert "profile" in test_connection_google.scopes_list
        assert test_connection_google.has_scope("email") is True
        assert test_connection_google.has_scope("calendar") is False
    
    def test_connection_to_dict(self, test_connection_google):
        """Test converting connection to dictionary."""
        conn_dict = test_connection_google.to_dict()
        
        assert conn_dict["id"] == test_connection_google.id
        assert conn_dict["provider"] == "google"
        assert conn_dict["is_active"] == True
        assert "access_token" not in conn_dict  # Should not include tokens


class TestWorkflowModel:
    """Tests for Workflow model."""
    
    def test_workflow_creation(self, db_session, test_tenant, test_user):
        """Test creating a workflow."""
        workflow = Workflow(
            tenant_id=test_tenant.id,
            created_by=test_user.id,
            name="Test Workflow",
            description="Test description",
            workflow_type=WorkflowType.POST_MEETING_FOLLOWUP,
            config={"key": "value"},
            is_active=True,
            status=WorkflowStatus.ACTIVE,
            priority=5,
        )
        db_session.add(workflow)
        db_session.commit()
        
        assert workflow.id is not None
        assert workflow.name == "Test Workflow"
        assert workflow.workflow_type == WorkflowType.POST_MEETING_FOLLOWUP
        assert workflow.is_active is True
        assert workflow.priority == 5
    
    def test_workflow_default_config(self):
        """Test getting default config for workflow types."""
        config = Workflow.get_default_config(WorkflowType.POST_MEETING_FOLLOWUP)
        
        assert config["create_crm_note"] is True
        assert config["draft_email"] is True
        assert config["create_task"] is True
    
    def test_workflow_to_dict(self, test_workflow):
        """Test converting workflow to dictionary."""
        workflow_dict = test_workflow.to_dict()
        
        assert workflow_dict["id"] == test_workflow.id
        assert workflow_dict["name"] == test_workflow.name
        assert workflow_dict["workflow_type"] == test_workflow.workflow_type.value


class TestWorkflowRunModel:
    """Tests for WorkflowRun model."""
    
    def test_workflow_run_creation(self, db_session, test_tenant, test_user, test_workflow):
        """Test creating a workflow run."""
        workflow_run = WorkflowRun(
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            workflow_id=test_workflow.id,
            trigger_type=WorkflowRunTriggerType.MANUAL,
            trigger_data={"event_id": "test_123"},
            status=WorkflowRunStatus.PENDING,
            total_tokens=0,
            total_duration_ms=0,
            idempotency_key="test_key",
        )
        db_session.add(workflow_run)
        db_session.commit()
        
        assert workflow_run.id is not None
        assert workflow_run.status == WorkflowRunStatus.PENDING
        assert workflow_run.trigger_type == WorkflowRunTriggerType.MANUAL
    
    def test_workflow_run_is_completed(self, test_workflow_run):
        """Test workflow run completion check."""
        assert test_workflow_run.is_completed is True
        
        # Test with non-completed status
        test_workflow_run.status = WorkflowRunStatus.RUNNING
        assert test_workflow_run.is_completed is False
    
    def test_workflow_run_is_active(self, test_workflow_run):
        """Test workflow run active check."""
        # Completed run is not active
        assert test_workflow_run.is_active is False
        
        # Running run is active
        test_workflow_run.status = WorkflowRunStatus.RUNNING
        assert test_workflow_run.is_active is True
    
    def test_workflow_run_duration(self, test_workflow_run):
        """Test workflow run duration calculation."""
        test_workflow_run.total_duration_ms = 2500
        assert test_workflow_run.duration_seconds == 2.5
    
    def test_workflow_run_to_dict(self, test_workflow_run):
        """Test converting workflow run to dictionary."""
        run_dict = test_workflow_run.to_dict()
        
        assert run_dict["id"] == test_workflow_run.id
        assert run_dict["status"] == test_workflow_run.status.value
        assert run_dict["total_tokens"] == test_workflow_run.total_tokens


class TestWorkflowStepModel:
    """Tests for WorkflowStep model."""
    
    def test_workflow_step_creation(self, db_session, test_workflow_run):
        """Test creating a workflow step."""
        step = WorkflowStep(
            run_id=test_workflow_run.id,
            step_type=WorkflowStepType.TOOL,
            step_name="Test Step",
            tool_name="test_tool",
            status=WorkflowStepStatus.PENDING,
            order=0,
        )
        db_session.add(step)
        db_session.commit()
        
        assert step.id is not None
        assert step.step_type == WorkflowStepType.TOOL
        assert step.status == WorkflowStepStatus.PENDING
    
    def test_workflow_step_is_completed(self, test_workflow_step):
        """Test workflow step completion check."""
        assert test_workflow_step.is_completed is True
        
        # Test with non-completed status
        test_workflow_step.status = WorkflowStepStatus.RUNNING
        assert test_workflow_step.is_completed is False
    
    def test_workflow_step_is_active(self, test_workflow_step):
        """Test workflow step active check."""
        # Completed step is not active
        assert test_workflow_step.is_active is False
        
        # Running step is active
        test_workflow_step.status = WorkflowStepStatus.RUNNING
        assert test_workflow_step.is_active is True
    
    def test_workflow_step_duration(self, test_workflow_step):
        """Test workflow step duration calculation."""
        test_workflow_step.latency_ms = 500
        assert test_workflow_step.duration_seconds == 0.5
    
    def test_workflow_step_to_dict(self, test_workflow_step):
        """Test converting workflow step to dictionary."""
        step_dict = test_workflow_step.to_dict()
        
        assert step_dict["id"] == test_workflow_step.id
        assert step_dict["step_type"] == test_workflow_step.step_type.value
        assert step_dict["status"] == test_workflow_step.status.value


class TestArtifactModel:
    """Tests for Artifact model."""
    
    def test_artifact_creation(self, db_session, test_workflow_run):
        """Test creating an artifact."""
        artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.CRM_NOTE,
            external_id="hubspot_123",
            external_url="https://hubspot.com/note/123",
            status=ArtifactStatus.CREATED,
            content_summary="Test note",
        )
        db_session.add(artifact)
        db_session.commit()
        
        assert artifact.id is not None
        assert artifact.artifact_type == ArtifactType.CRM_NOTE
        assert artifact.status == ArtifactStatus.CREATED
    
    def test_artifact_is_file(self, db_session, test_workflow_run):
        """Test artifact file check."""
        file_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.FILE,
        )
        db_session.add(file_artifact)
        db_session.commit()
        
        assert file_artifact.is_file is True
        
        crm_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.CRM_NOTE,
        )
        db_session.add(crm_artifact)
        db_session.commit()
        
        assert crm_artifact.is_file is False
    
    def test_artifact_is_crm(self, db_session, test_workflow_run):
        """Test artifact CRM check."""
        crm_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.CRM_NOTE,
        )
        db_session.add(crm_artifact)
        db_session.commit()
        
        assert crm_artifact.is_crm is True
        
        email_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.EMAIL_DRAFT,
        )
        db_session.add(email_artifact)
        db_session.commit()
        
        assert email_artifact.is_crm is False
    
    def test_artifact_is_email(self, db_session, test_workflow_run):
        """Test artifact email check."""
        email_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.EMAIL_DRAFT,
        )
        db_session.add(email_artifact)
        db_session.commit()
        
        assert email_artifact.is_email is True
        
        crm_artifact = Artifact(
            run_id=test_workflow_run.id,
            artifact_type=ArtifactType.CRM_NOTE,
        )
        db_session.add(crm_artifact)
        db_session.commit()
        
        assert crm_artifact.is_email is False
    
    def test_artifact_to_dict(self, test_artifact):
        """Test converting artifact to dictionary."""
        artifact_dict = test_artifact.to_dict()
        
        assert artifact_dict["id"] == test_artifact.id
        assert artifact_dict["artifact_type"] == test_artifact.artifact_type.value
        assert artifact_dict["status"] == test_artifact.status.value
