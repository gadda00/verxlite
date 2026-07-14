"""
Tests for API Routes
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for root/health endpoints."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Verxlite API"
        assert body["version"] == "0.1.0"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        # Health is allowed to be degraded (Redis may not be available in CI),
        # but the endpoint itself must always return 200.
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert "checks" in body
        assert "database" in body["checks"]
        assert "redis" in body["checks"]


class TestAuthRoutes:
    """Tests for auth routes."""

    def test_register_user(self, client, db_session):
        # Clean up any prior user with the same email.
        from verxlite_api.models.user import User
        existing = db_session.query(User).filter(User.email == "newuser@example.com").first()
        if existing:
            db_session.delete(existing)
            db_session.commit()

        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "supersecret123",
                "first_name": "New",
                "last_name": "User",
                "tenant_name": "New Tenant",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "newuser@example.com"

    def test_register_user_short_password_rejected(self, client, db_session):
        response = client.post(
            "/auth/register",
            json={"email": "short@example.com", "password": "abc"},
        )
        assert response.status_code == 422

    def test_login_user(self, client, test_user):
        # test_user has password "testpassword123" (set in conftest).
        response = client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "testpassword123"},
        )
        assert response.status_code == 200, response.text
        assert "access_token" in response.json()

    def test_login_user_wrong_password(self, client, test_user):
        response = client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_user_unknown_email(self, client):
        response = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "anything"},
        )
        assert response.status_code == 401

    def test_get_current_user_unauthenticated(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_get_current_user_authenticated(self, client, auth_headers, test_user):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["email"] == test_user.email


class TestWorkflowRoutes:
    """Tests for workflow routes (all require auth)."""

    def test_list_workflows_unauthenticated(self, client):
        response = client.get("/workflows/")
        assert response.status_code == 401

    def test_list_workflows(self, client, auth_headers):
        response = client.get("/workflows/", headers=auth_headers)
        assert response.status_code == 200
        assert "workflows" in response.json()

    def test_create_workflow(self, client, auth_headers):
        response = client.post(
            "/workflows/",
            headers=auth_headers,
            json={
                "name": "Test Workflow",
                "description": "Test description",
                "workflow_type": "post_meeting_followup",
                "config": {},
                "priority": 5,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["name"] == "Test Workflow"

    def test_create_workflow_invalid_priority(self, client, auth_headers):
        response = client.post(
            "/workflows/",
            headers=auth_headers,
            json={"name": "Bad", "workflow_type": "post_meeting_followup", "priority": 99},
        )
        assert response.status_code == 422

    def test_list_workflow_templates(self, client, auth_headers):
        response = client.get("/workflows/templates", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 3

    def test_get_workflow_stats(self, client, auth_headers):
        response = client.get("/workflows/stats", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert "total_runs" in body

    def test_trigger_workflow_run(self, client, auth_headers, test_workflow):
        # test_workflow was created by the fixture in the test_user's tenant.
        # But wait — the test_workflow fixture creates a workflow directly via
        # the DB, so it lives in test_user's tenant. Authenticated client should
        # be able to trigger it.
        # However, the fixture isn't requested here. We need to create a workflow
        # via the API first.
        create_response = client.post(
            "/workflows/",
            headers=auth_headers,
            json={"name": "Trigger Test", "workflow_type": "post_meeting_followup"},
        )
        workflow_id = create_response.json()["id"]

        response = client.post(
            f"/workflows/{workflow_id}/runs",
            headers=auth_headers,
            json={"trigger_type": "manual", "trigger_data": {"event_id": "evt_1"}},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["status"] in ("queued", "running", "completed", "failed")

    def test_get_nonexistent_workflow(self, client, auth_headers):
        response = client.get("/workflows/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404


class TestConnectionRoutes:
    """Tests for connection routes (require auth)."""

    def test_list_connections(self, client, auth_headers):
        response = client.get("/connections/", headers=auth_headers)
        assert response.status_code == 200
        assert "connections" in response.json()

    def test_list_connections_unauthenticated(self, client):
        response = client.get("/connections/")
        assert response.status_code == 401


class TestArtifactRoutes:
    """Tests for artifact routes (require auth)."""

    def test_list_artifacts(self, client, auth_headers):
        response = client.get("/artifacts/", headers=auth_headers)
        assert response.status_code == 200
        assert "artifacts" in response.json()

    def test_list_artifacts_unauthenticated(self, client):
        response = client.get("/artifacts/")
        assert response.status_code == 401


class TestErrorHandling:
    """Tests for error handling."""

    def test_not_found_error(self, client, auth_headers):
        # /workflows/{workflow_id} requires auth; provide it.
        response = client.get("/workflows/nonexistent", headers=auth_headers)
        assert response.status_code == 404
        assert "error" in response.json()
        assert response.json()["error"] == "NotFoundError"

    def test_validation_error(self, client, auth_headers):
        # Empty name should fail validation.
        response = client.post(
            "/workflows/",
            headers=auth_headers,
            json={"name": ""},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "ValidationError"
