"""Tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers with valid API key."""
    return {"X-API-Key": "test-api-key"}


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Should return health status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_liveness(self, client):
        """Should return liveness status."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness(self, client):
        """Should return readiness status."""
        response = client.get("/health/ready")
        
        # Might fail if no DB, but should return valid response
        assert response.status_code in (200, 503)


class TestIncidentEndpoints:
    """Tests for incident management endpoints."""
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_create_incident_requires_auth(self, client):
        """Should require API key for incident creation."""
        response = client.post(
            "/api/v1/incidents",
            json={
                "title": "Test incident",
                "source": "test",
                "repository": {
                    "url": "https://github.com/test/repo",
                    "branch": "main",
                },
            },
        )
        
        assert response.status_code in (401, 403)
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_create_incident_with_auth(self, client, auth_headers):
        """Should create incident with valid auth."""
        response = client.post(
            "/api/v1/incidents",
            headers=auth_headers,
            json={
                "title": "Test incident",
                "source": "test",
                "repository": {
                    "url": "https://github.com/test/repo",
                    "branch": "main",
                },
            },
        )
        
        assert response.status_code in (200, 201, 202)


class TestWebhookEndpoints:
    """Tests for webhook handling."""
    
    def test_github_webhook_requires_signature(self, client):
        """GitHub webhook should require valid signature."""
        response = client.post(
            "/api/v1/webhooks/github",
            json={"action": "completed"},
        )
        
        # Should fail without signature
        assert response.status_code in (400, 401, 403)
    
    def test_datadog_webhook_format(self, client):
        """Datadog webhook should accept monitor alerts."""
        # This is a simplified test - real webhook would need auth
        response = client.post(
            "/api/v1/webhooks/datadog",
            json={
                "event_type": "test",
                "alert_type": "info",
            },
        )
        
        # Should at least parse the request
        assert response.status_code != 500


class TestAPIDocumentation:
    """Tests for API documentation."""
    
    def test_openapi_schema(self, client):
        """Should expose OpenAPI schema."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
    
    def test_docs_endpoint(self, client):
        """Should serve API documentation."""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
