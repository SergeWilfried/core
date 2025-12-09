"""
End-to-end tests for API endpoints
"""

import pytest
from httpx import AsyncClient

from core.api.app import app


@pytest.mark.asyncio
class TestAPIEndpoints:
    """E2E tests for API endpoints"""

    async def test_root_endpoint(self):
        """Test root endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "BaaS Core Banking API"

    async def test_health_check(self):
        """Test health check endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    async def test_create_account_unauthorized(self):
        """Test creating account without authentication"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/accounts/",
                json={
                    "customer_id": "cust_123",
                    "account_type": "checking",
                    "currency": "USD",
                },
            )
            # Should require authentication
            assert response.status_code == 403
