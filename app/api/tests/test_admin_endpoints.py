import pytest
import json
import httpx
import asyncio
from uuid import UUID
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v6"
ADMIN_EMAIL = "admin@agritech.com"
ADMIN_PASSWORD = "admin123"

async def get_admin_token():
    """Get admin authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        data = response.json()
        return data["data"]["access"]

@pytest.mark.asyncio
async def test_admin_endpoints():
    """Test all admin endpoints"""
    
    # Get admin token
    token = await get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Test List All Users
        response = await client.get(f"{BASE_URL}/admin/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Save first user ID for later tests
        first_user_id = data["data"][0]["id"] if data["data"] else None
        
        # 2. Test Get User Details
        if first_user_id:
            response = await client.get(
                f"{BASE_URL}/admin/users/{first_user_id}",
                headers=headers
            )
            logger.info(f"Get user details response: {response.text}")
            if response.status_code != 200:
                logger.error(f"User details failed with status {response.status_code}: {response.text}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            user_data = data["data"]
            
            # Validate required fields
            assert str(user_data["id"]) == str(first_user_id)
            assert isinstance(user_data["email"], str)
            assert isinstance(user_data["role"], str)
            assert user_data["role"] in ["FARMER", "TRADER", "ADMIN"]
            assert isinstance(user_data["is_verified"], bool)
            assert isinstance(user_data["is_active"], bool)
            assert isinstance(user_data["total_listings"], int)
            assert isinstance(user_data["total_bids"], int)
            assert isinstance(user_data["total_purchases"], int)        # 3. Test Update User Verification
        if first_user_id:
            response = await client.patch(
                f"{BASE_URL}/admin/users/{first_user_id}/verification",
                headers=headers,
                json={
                    "is_verified": True,
                    "verification_notes": "Approved in testing"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["is_verified"] is True
        
        # 4. Test Active Bids Statistics
        response = await client.get(f"{BASE_URL}/admin/active-bids", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        
        # 5. Test Commodities Statistics
        response = await client.get(f"{BASE_URL}/admin/commodities/count", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        
        # 6. Test Platform Statistics
        response = await client.get(f"{BASE_URL}/admin/stats/platform", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        
        # 7. Test Get Pending Commodities
        response = await client.get(f"{BASE_URL}/admin/pending-commodities/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data

async def test_admin_error_cases():
    """Test error cases for admin endpoints"""
    
    # Get admin token
    token = await get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Test non-existent user
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"{BASE_URL}/admin/users/{fake_uuid}",
            headers=headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "failure"
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        
        # 2. Test invalid verification data - missing required field
        response = await client.patch(
            f"{BASE_URL}/admin/users/{fake_uuid}/verification",
            headers=headers,
            json={"verification_notes": "Test note"}  # Missing is_verified field
        )
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "failure"
        assert "detail" in data
        
        # 3. Test invalid verification data - wrong field name
        response = await client.patch(
            f"{BASE_URL}/admin/users/{fake_uuid}/verification",
            headers=headers,
            json={"is_email_verified": True}  # Wrong field name
        )
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "failure"
        assert "detail" in data

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
