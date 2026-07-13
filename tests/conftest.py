"""
Pytest Configuration and Fixtures
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verxlite_api.db.base import Base
from verxlite_api.models.tenant import Tenant
from verxlite_api.models.user import User
from verxlite_api.models.connection import Connection
from verxlite_api.models.workflow import Workflow, WorkflowType, WorkflowStatus
from verxlite_api.models.workflow_run import WorkflowRun, WorkflowRunStatus, WorkflowRunTriggerType
from verxlite_api.models.workflow_step import WorkflowStep, WorkflowStepStatus, WorkflowStepType
from verxlite_api.models.artifact import Artifact, ArtifactType, ArtifactStatus

# Create test database
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        description="Test tenant for pytest",
        domain="test.com",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.id,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role="admin",
        is_active=True,
        clerk_id="clerk_test_123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_connection_google(db_session, test_tenant, test_user):
    """Create a test Google connection."""
    connection = Connection(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="google",
        provider_user_id="google_user_123",
        access_token="encrypted_access_token",
        refresh_token="encrypted_refresh_token",
        token_type="Bearer",
        expires_at=None,
        scope="email,profile,calendar.readonly",
        is_active=True,
        metadata={"user_info": {"email": "test@example.com"}},
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


@pytest.fixture
def test_connection_hubspot(db_session, test_tenant, test_user):
    """Create a test HubSpot connection."""
    connection = Connection(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        provider="hubspot",
        provider_user_id=None,
        access_token="encrypted_access_token",
        refresh_token="encrypted_refresh_token",
        token_type="Bearer",
        expires_at=None,
        scope="contacts,content,automation",
        is_active=True,
        metadata={},
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


@pytest.fixture
def test_workflow(db_session, test_tenant, test_user):
    """Create a test workflow."""
    workflow = Workflow(
        tenant_id=test_tenant.id,
        created_by=test_user.id,
        name="Test Workflow",
        description="Test workflow for pytest",
        workflow_type=WorkflowType.POST_MEETING_FOLLOWUP,
        config={"create_crm_note": True, "draft_email": True},
        is_active=True,
        status=WorkflowStatus.ACTIVE,
        trigger_config={},
        priority=5,
    )
    db_session.add(workflow)
    db_session.commit()
    db_session.refresh(workflow)
    return workflow


@pytest.fixture
def test_workflow_run(db_session, test_tenant, test_user, test_workflow):
    """Create a test workflow run."""
    workflow_run = WorkflowRun(
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        workflow_id=test_workflow.id,
        trigger_type=WorkflowRunTriggerType.MANUAL,
        trigger_data={"event_id": "test_event_123"},
        status=WorkflowRunStatus.COMPLETED,
        total_tokens=1500,
        total_duration_ms=2500,
        total_cost=0.5,
        idempotency_key="test_idempotency_key",
        retry_count=0,
    )
    db_session.add(workflow_run)
    db_session.commit()
    db_session.refresh(workflow_run)
    return workflow_run


@pytest.fixture
def test_workflow_step(db_session, test_workflow_run):
    """Create a test workflow step."""
    step = WorkflowStep(
        run_id=test_workflow_run.id,
        step_type=WorkflowStepType.TOOL,
        step_name="Test Step",
        tool_name="test_tool",
        status=WorkflowStepStatus.COMPLETED,
        input_summary="Test input",
        output_summary="Test output",
        input_data={"key": "value"},
        output_data={"result": "success"},
        latency_ms=500,
        tokens_used=100,
        order=0,
        retry_count=0,
        max_retries=3,
        timeout_ms=30000,
    )
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)
    return step


@pytest.fixture
def test_artifact(db_session, test_workflow_run):
    """Create a test artifact."""
    artifact = Artifact(
        run_id=test_workflow_run.id,
        artifact_type=ArtifactType.CRM_NOTE,
        external_id="hubspot_note_123",
        external_url="https://hubspot.com/note/123",
        status=ArtifactStatus.COMPLETED,
        content_summary="Test CRM note",
        content_data={"body": "Test note content"},
        metadata={"contact_id": "contact_123"},
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)
    return artifact


# Mock external API responses
@pytest.fixture
def mock_google_api():
    """Mock Google API responses."""
    pass


@pytest.fixture
def mock_hubspot_api():
    """Mock HubSpot API responses."""
    pass
