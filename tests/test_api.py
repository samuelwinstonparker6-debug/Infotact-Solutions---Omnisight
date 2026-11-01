"""
OmniSight — API Endpoint Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tests for the FastAPI health check and API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
async def client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Test root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "OmniSight" in data["message"]


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "OmniSight"
    assert "version" in data
    assert "checks" in data


@pytest.mark.asyncio
async def test_api_status(client: AsyncClient):
    """Test API v1 status endpoint."""
    response = await client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "services" in data


from unittest.mock import patch

@pytest.mark.asyncio
async def test_scan_success(client: AsyncClient):
    """Test scan endpoint returns accepted status and run_id."""
    with patch("backend.api.routes.run_scan_background_task"):
        response = await client.post(
            "/api/v1/scan",
            json={"url": "http://localhost:8000/mock-app/index.html", "auto_fix": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert "run_id" in data
        assert data["url"] == "http://localhost:8000/mock-app/index.html"


@pytest.mark.asyncio
async def test_list_runs_empty(client: AsyncClient):
    """Test list runs endpoint returns correctly."""
    response = await client.get("/api/v1/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["runs"], list)
    assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_stop_scan_endpoints(client: AsyncClient):
    """Test stopping an active scan by run_id and stopping all active scans."""
    with patch("backend.api.routes.run_scan_background_task"):
        # 1. Trigger a scan
        scan_res = await client.post(
            "/api/v1/scan",
            json={"url": "http://localhost:8000/mock-app/index.html"}
        )
        assert scan_res.status_code == 200
        run_id = scan_res.json()["run_id"]

        # 2. Stop this scan
        stop_res = await client.post(f"/api/v1/scan/{run_id}/stop")
        assert stop_res.status_code == 200
        stop_data = stop_res.json()
        assert stop_data["status"] == "success"
        assert stop_data["run_id"] == run_id

        # 3. Stop all scans
        stop_all_res = await client.post("/api/v1/scan/stop")
        assert stop_all_res.status_code == 200
        stop_all_data = stop_all_res.json()
        assert stop_all_data["status"] == "success"
        assert "stopped_run_ids" in stop_all_data
