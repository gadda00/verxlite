"""
Tests for API Routes
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_endpoint(self):
        """Test GET / endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "name" in response.json()
        assert response.json()["name"] == "Verxlite API"
        assert "version" in response.json()
    
    def test_health_endpoint(self):
        """Test GET /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"


class TestAuthRoutes:
    """Tests for auth routes."""
    
    def test_register_user(self):
        """Test POST /auth/register endpoint."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "tenant_name": "Test Tenant",
            },
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "user" in response.json()
    
    def test_login_user(self):
        """Test POST /auth/login endpoint."""
        # First register a user
        client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword",
            },
        )
        
        # Then login
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword",
            },
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_get_current_user(self):
        """Test GET /auth/me endpoint."""
        # First register and login
        login_response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword",
            },
        )
        
        access_token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        assert "email" in response.json()


class TestWorkflowRoutes:
    """Tests for workflow routes."""
    
    def test_list_workflows(self):
        """Test GET /workflows/ endpoint."""
        response = client.get("/workflows/")
        
        assert response.status_code == 200
        assert "workflows" in response.json()
    
    def test_create_workflow(self):
        """Test POST /workflows/ endpoint."""
        response = client.post(
            "/workflows/",
            json={
                "name": "Test Workflow",
                "description": "Test description",
                "workflow_type": "post_meeting_followup",
                "config": {},
                "priority": 5,
            },
        )
        
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == "Test Workflow"
    
    def test_trigger_workflow_run(self):
        """Test POST /workflows/{workflow_id}/runs endpoint."""
        # First create a workflow
        create_response = client.post(
            "/workflows/",
            json={
                "name": "Test Workflow",
                "workflow_type": "post_meeting_followup",
            },
        )
        
        workflow_id = create_response.json()["id"]
        
        # Trigger a run
        response = client.post(
            f"/workflows/{workflow_id}/runs",
            json={
                "trigger_type": "manual",
                "trigger_data": {},
            },
        )
        
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["status"] == "queued"


class TestConnectionRoutes:
    """Tests for connection routes."""
    
    def test_list_connections(self):
        """Test GET /connections/ endpoint."""
        response = client.get("/connections/")
        
        assert response.status_code == 200
        assert "connections" in response.json()


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_not_found_error(self):
        """Test 404 error handling."""
        response = client.get("/workflows/nonexistent")
        
        assert response.status_code == 404
        assert "error" in response.json()
    
    def test_validation_error(self):
        """Test validation error handling."""
        response = client.post(
            "/workflows/",
            json={
                "name": "",  # Empty name should fail validation
            },
        )
        
        assert response.status_code == 422
        assert "error" in response.json()
        assert response.json()["error"] == "ValidationError"
