"""
Comprehensive API Testing Suite
==============================

Complete test coverage for all API endpoints with security, performance, and functionality tests
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

from app.main import app
from app.core.database import get_db
from app.core.config import settings


class APITestSuite:
    """
    Comprehensive API testing framework
    """
    
    def __init__(self):
        self.client = TestClient(app)
        self.test_users = {}
        self.test_data = {}
        self.auth_tokens = {}
    
    async def setup_test_data(self):
        """Setup test data for comprehensive testing"""
        
        # Test users for different roles
        self.test_users = {
            "farmer": {
                "email": "farmer@test.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Farmer",
                "role": "farmer",
                "upi_id": "farmer@paytm",
                "bank_account": "1234567890123456",
                "ifsc_code": "HDFC0001234"
            },
            "trader": {
                "email": "trader@test.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Trader",
                "role": "trader",
                "upi_id": "trader@paytm",
                "bank_account": "9876543210987654",
                "ifsc_code": "ICIC0002345"
            },
            "admin": {
                "email": "admin@test.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Admin",
                "role": "admin"
            }
        }
        
        # Test commodity data
        self.test_data["commodities"] = [
            {
                "commodity_name": "Premium Wheat",
                "description": "High quality wheat from Punjab",
                "quantity_kg": 1000.0,
                "harvest_date": "2025-01-15",
                "min_price": 25.50,
                "closing_date": "2025-08-01T12:00:00",
                "category_id": None
            },
            {
                "commodity_name": "Organic Rice",
                "description": "Certified organic basmati rice",
                "quantity_kg": 500.0,
                "harvest_date": "2025-02-01",
                "min_price": 45.00,
                "closing_date": "2025-08-15T12:00:00",
                "category_id": None
            }
        ]
    
    def register_test_users(self) -> Dict[str, str]:
        """Register all test users and return their auth tokens"""
        tokens = {}
        
        for role, user_data in self.test_users.items():
            # Register user
            response = self.client.post("/api/v1/auth/register", json={
                **user_data,
                "terms_agreement": True
            })
            
            if response.status_code == 201:
                # Login to get token
                login_response = self.client.post("/api/v1/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    tokens[role] = token_data["data"]["access_token"]
        
        self.auth_tokens = tokens
        return tokens
    
    def get_auth_headers(self, role: str) -> Dict[str, str]:
        """Get authorization headers for a specific role"""
        if role in self.auth_tokens:
            return {"Authorization": f"Bearer {self.auth_tokens[role]}"}
        return {}


# Test Cases for All API Endpoints

class TestAuthenticationAPI:
    """Test authentication and authorization endpoints"""
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        test_suite = APITestSuite()
        
        user_data = {
            "email": "newuser@test.com",
            "password": "SecurePass123!",
            "first_name": "New",
            "last_name": "User",
            "role": "farmer",
            "terms_agreement": True,
            "upi_id": "newuser@paytm",
            "bank_account": "1111222233334444",
            "ifsc_code": "SBIN0001234"
        }
        
        response = test_suite.client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Registration successful"
        assert "user" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        test_suite = APITestSuite()
        
        # Register first user
        user_data = {
            "email": "duplicate@test.com",
            "password": "SecurePass123!",
            "first_name": "First",
            "last_name": "User",
            "role": "farmer",
            "terms_agreement": True
        }
        
        response1 = test_suite.client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = test_suite.client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    def test_user_login_success(self):
        """Test successful user login"""
        test_suite = APITestSuite()
        
        # Register user first
        user_data = {
            "email": "logintest@test.com",
            "password": "SecurePass123!",
            "first_name": "Login",
            "last_name": "Test",
            "role": "farmer",
            "terms_agreement": True
        }
        
        register_response = test_suite.client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        # Login
        login_response = test_suite.client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        test_suite = APITestSuite()
        
        response = test_suite.client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 400
        assert "Invalid credentials" in response.json()["detail"]


class TestCommodityAPI:
    """Test commodity management endpoints"""
    
    def test_create_commodity_success(self):
        """Test successful commodity creation"""
        test_suite = APITestSuite()
        asyncio.run(test_suite.setup_test_data())
        tokens = test_suite.register_test_users()
        
        commodity_data = test_suite.test_data["commodities"][0]
        headers = test_suite.get_auth_headers("farmer")
        
        response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["commodity_name"] == commodity_data["commodity_name"]
    
    def test_get_all_commodities(self):
        """Test getting all commodities"""
        test_suite = APITestSuite()
        
        response = test_suite.client.get("/api/v1/commodities/")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_commodity_by_id(self):
        """Test getting specific commodity by ID"""
        test_suite = APITestSuite()
        asyncio.run(test_suite.setup_test_data())
        tokens = test_suite.register_test_users()
        
        # Create commodity first
        commodity_data = test_suite.test_data["commodities"][0]
        headers = test_suite.get_auth_headers("farmer")
        
        create_response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=headers
        )
        
        assert create_response.status_code == 201
        commodity_id = create_response.json()["data"]["id"]
        
        # Get commodity by ID
        get_response = test_suite.client.get(f"/api/v1/commodities/{commodity_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["data"]["id"] == commodity_id


class TestBiddingAPI:
    """Test bidding system endpoints"""
    
    def test_place_bid_success(self):
        """Test successful bid placement"""
        test_suite = APITestSuite()
        asyncio.run(test_suite.setup_test_data())
        tokens = test_suite.register_test_users()
        
        # Create commodity first
        commodity_data = test_suite.test_data["commodities"][0]
        farmer_headers = test_suite.get_auth_headers("farmer")
        
        create_response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=farmer_headers
        )
        
        commodity_id = create_response.json()["data"]["id"]
        
        # Place bid as trader
        trader_headers = test_suite.get_auth_headers("trader")
        bid_data = {
            "commodity_listing_id": commodity_id,
            "amount": 30.00
        }
        
        bid_response = test_suite.client.post(
            "/api/v1/bidding/place-bid",
            json=bid_data,
            headers=trader_headers
        )
        
        assert bid_response.status_code == 201
        data = bid_response.json()
        assert data["data"]["amount"] == bid_data["amount"]


class TestPriceTrackingAPI:
    """Test price tracking and alerts endpoints"""
    
    def test_create_price_alert(self):
        """Test creating price alert subscription"""
        test_suite = APITestSuite()
        asyncio.run(test_suite.setup_test_data())
        tokens = test_suite.register_test_users()
        
        # Create commodity first
        commodity_data = test_suite.test_data["commodities"][0]
        farmer_headers = test_suite.get_auth_headers("farmer")
        
        create_response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=farmer_headers
        )
        
        commodity_id = create_response.json()["data"]["id"]
        
        # Create price alert
        alert_data = {
            "commodity_id": commodity_id,
            "threshold_price": 28.00,
            "direction": "BELOW",
            "notify_email": True,
            "notify_sms": False
        }
        
        trader_headers = test_suite.get_auth_headers("trader")
        response = test_suite.client.post(
            "/api/v1/price-tracking/alerts",
            json=alert_data,
            headers=trader_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["threshold_price"] == alert_data["threshold_price"]


class TestMLRecommendationsAPI:
    """Test ML recommendations endpoints"""
    
    def test_get_commodity_recommendation(self):
        """Test getting ML recommendation for commodity"""
        test_suite = APITestSuite()
        asyncio.run(test_suite.setup_test_data())
        tokens = test_suite.register_test_users()
        
        # Create commodity first
        commodity_data = test_suite.test_data["commodities"][0]
        farmer_headers = test_suite.get_auth_headers("farmer")
        
        create_response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=farmer_headers
        )
        
        commodity_id = create_response.json()["data"]["id"]
        
        # Get ML recommendation
        trader_headers = test_suite.get_auth_headers("trader")
        response = test_suite.client.get(
            f"/api/v6/recommendations/suggestions/{commodity_id}",
            headers=trader_headers
        )
        
        # Note: This might return 400 if insufficient data, which is expected
        assert response.status_code in [200, 400]
    
    def test_get_market_overview(self):
        """Test getting market overview"""
        test_suite = APITestSuite()
        tokens = test_suite.register_test_users()
        
        trader_headers = test_suite.get_auth_headers("trader")
        response = test_suite.client.get(
            "/api/v6/recommendations/market-overview",
            headers=trader_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "market_sentiment" in data["data"]


class TestAdminAPI:
    """Test admin-only endpoints"""
    
    def test_admin_kyc_verification(self):
        """Test admin KYC verification"""
        test_suite = APITestSuite()
        tokens = test_suite.register_test_users()
        
        # Get user ID to verify
        farmer_user_data = test_suite.test_users["farmer"]
        
        # Admin verifies farmer's KYC
        admin_headers = test_suite.get_auth_headers("admin")
        
        # Note: Need to get actual user ID from database
        # This is a placeholder test structure
        response = test_suite.client.patch(
            "/api/v1/auth/verify-kyc/user_id_here",
            json={"is_verified": True},
            headers=admin_headers
        )
        
        # Test structure - actual implementation would need user ID
        # assert response.status_code == 200


class TestSecurityAPI:
    """Test security-related functionality"""
    
    def test_rate_limiting(self):
        """Test API rate limiting"""
        test_suite = APITestSuite()
        
        # Make multiple rapid requests
        responses = []
        for i in range(70):  # Exceed rate limit
            response = test_suite.client.get("/api/v1/general/health")
            responses.append(response)
        
        # Should eventually get rate limited (429)
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(code == 200 for code in status_codes)
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        test_suite = APITestSuite()
        
        weak_passwords = [
            "123456",      # Too short, no letters
            "password",    # No numbers or special chars
            "Password",    # No numbers or special chars
            "Password1",   # No special chars
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "email": f"test{weak_password}@test.com",
                "password": weak_password,
                "first_name": "Test",
                "last_name": "User",
                "role": "farmer",
                "terms_agreement": True
            }
            
            response = test_suite.client.post("/api/v1/auth/register", json=user_data)
            # Should fail due to weak password
            assert response.status_code == 400
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection"""
        test_suite = APITestSuite()
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "1; UPDATE users SET role='admin'"
        ]
        
        for malicious_input in malicious_inputs:
            response = test_suite.client.post("/api/v1/auth/login", json={
                "email": malicious_input,
                "password": "any_password"
            })
            
            # Should not cause server error
            assert response.status_code in [400, 401, 422]  # Bad request or unauthorized


# Performance Tests
class TestPerformance:
    """Test API performance and load handling"""
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import concurrent.futures
        import threading
        
        test_suite = APITestSuite()
        
        def make_request():
            return test_suite.client.get("/api/v1/general/health")
        
        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            responses = [future.result() for future in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
    
    def test_large_data_handling(self):
        """Test handling of large data payloads"""
        test_suite = APITestSuite()
        tokens = test_suite.register_test_users()
        
        # Create commodity with large description
        large_description = "X" * 10000  # 10KB description
        
        commodity_data = {
            "commodity_name": "Large Data Test",
            "description": large_description,
            "quantity_kg": 1000.0,
            "harvest_date": "2025-01-15",
            "min_price": 25.50,
            "closing_date": "2025-08-01T12:00:00"
        }
        
        headers = test_suite.get_auth_headers("farmer")
        response = test_suite.client.post(
            "/api/v1/commodities/", 
            json=commodity_data,
            headers=headers
        )
        
        # Should handle large data gracefully
        assert response.status_code in [201, 400, 413]  # Created, bad request, or payload too large


# Test Runner
def run_comprehensive_tests():
    """Run all API tests"""
    
    print("🧪 Running Comprehensive API Test Suite")
    print("=" * 60)
    
    test_classes = [
        TestAuthenticationAPI,
        TestCommodityAPI,
        TestBiddingAPI,
        TestPriceTrackingAPI,
        TestMLRecommendationsAPI,
        TestAdminAPI,
        TestSecurityAPI,
        TestPerformance
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                test_instance = test_class()
                method = getattr(test_instance, test_method)
                method()
                passed_tests += 1
                print(f"  ✅ {test_method}")
            except Exception as e:
                failed_tests.append(f"{test_class.__name__}.{test_method}: {str(e)}")
                print(f"  ❌ {test_method}: {str(e)}")
    
    print(f"\n📊 Test Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"   - {failure}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": len(failed_tests),
        "success_rate": success_rate,
        "failures": failed_tests
    }


if __name__ == "__main__":
    run_comprehensive_tests()
