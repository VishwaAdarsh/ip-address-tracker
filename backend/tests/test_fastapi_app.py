"""
Unit & Integration Tests for Production FastAPI Application (Render ASGI).
"""
import pytest
from starlette.testclient import TestClient

from backend.api.fastapi_app import create_fastapi_app


@pytest.fixture(scope="module")
def client():
    """Create test client for FastAPI application."""
    app = create_fastapi_app()
    with TestClient(app) as test_client:
        yield test_client


def test_fastapi_instance():
    """Verify application is a valid FastAPI instance."""
    app = create_fastapi_app()
    assert app.title.startswith("IP PULSE")
    assert app.version == "2.0.0"


def test_api_status_endpoint(client):
    """Verify /api/status returns operational status and capabilities."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["capabilities"]["geolocation"] is True
    assert data["capabilities"]["risk_engine"] is True


def test_api_history_endpoint(client):
    """Verify /api/history returns record list."""
    response = client.get("/api/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["records"], list)


def test_api_field_study_endpoint(client):
    """Verify /api/field-study returns quota and summary."""
    response = client.get("/api/field-study")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["target"] == 50
    assert "available_count" in data


def test_api_analytics_endpoint(client):
    """Verify /api/analytics returns statistical calculations."""
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "total_observations" in data


def test_frontend_root_delivery(client):
    """Verify root GET serves the Stitch web interface."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "IP PULSE" in response.text


def test_cors_vercel_origin(client):
    """Verify CORS headers correctly allow Vercel domains."""
    response = client.get("/api/status", headers={"Origin": "https://ip-pulse-vishwa.vercel.app"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://ip-pulse-vishwa.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_localhost_origin(client):
    """Verify CORS headers correctly allow local Vite dev origin."""
    response = client.get("/api/status", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_options_preflight(client):
    """Verify CORS preflight OPTIONS requests are handled successfully."""
    response = client.options(
        "/api/status",
        headers={
            "Origin": "https://ip-pulse-vishwa.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://ip-pulse-vishwa.vercel.app"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
