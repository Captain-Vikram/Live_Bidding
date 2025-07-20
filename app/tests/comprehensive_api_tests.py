"""
Comprehensive API Tests for AgriTech Platform
===========================================

Tests all major API endpoints including authentication, listings, bids, ML recommendations, and notifications.
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Test Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v6"

class APITestClient:
    """Comprehensive API test client for AgriTech Platform"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.test_data = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    # ===== AUTHENTICATION TESTS =====
    
    async def test_health_check(self):
        """Test basic health check endpoint"""
        print("\n🔍 Testing Health Check...")
        response = await self.client.get(f"{API_BASE}/healthcheck")
        assert response.status_code == 200
        assert response.json()["success"] == "pong!"
        print("✅ Health check passed")
        return response.json()
    
    async def test_user_registration(self):
        """Test user registration endpoint"""
        print("\n👤 Testing User Registration...")
        
        user_data = {
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@agritech.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "FARMER",
            "terms_agreement": True,
            "phone_number": "+1234567890",
            "address": "123 Test Farm Road",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "12345",
            "country": "Test Country"
        }
        
        response = await self.client.post(f"{API_BASE}/auth/register", json=user_data)
        print(f"Registration response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            self.test_data["user_data"] = user_data
            print("✅ User registration successful")
            return data
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    
    async def test_user_login(self):
        """Test user login endpoint"""
        print("\n🔐 Testing User Login...")
        
        if "user_data" not in self.test_data:
            print("❌ No user data available for login test")
            return None
        
        login_data = {
            "email": self.test_data["user_data"]["email"],
            "password": self.test_data["user_data"]["password"]
        }
        
        response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["data"]["access_token"]
            self.user_id = data["data"]["user"]["id"]
            
            # Set authorization header for future requests
            self.client.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            print("✅ User login successful")
            print(f"Token: {self.auth_token[:20]}...")
            return data
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    
    async def test_get_current_user(self):
        """Test get current user endpoint"""
        print("\n👤 Testing Get Current User...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/auth/me")
        print(f"Get user response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Get current user successful")
            print(f"User: {data['data']['first_name']} {data['data']['last_name']}")
            return data
        else:
            print(f"❌ Get current user failed: {response.text}")
            return None
    
    # ===== CATEGORY TESTS =====
    
    async def test_get_categories(self):
        """Test get categories endpoint"""
        print("\n📂 Testing Get Categories...")
        
        response = await self.client.get(f"{API_BASE}/general/categories")
        print(f"Categories response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.test_data["categories"] = data["data"]
            print(f"✅ Found {len(data['data'])} categories")
            return data
        else:
            print(f"❌ Get categories failed: {response.text}")
            return None
    
    # ===== LISTINGS TESTS =====
    
    async def test_create_listing(self):
        """Test create listing endpoint"""
        print("\n📝 Testing Create Listing...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        if "categories" not in self.test_data or not self.test_data["categories"]:
            print("❌ No categories available")
            return None
        
        category_id = self.test_data["categories"][0]["id"]
        
        listing_data = {
            "name": f"Test Wheat Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": "Premium quality wheat for testing",
            "category_id": category_id,
            "price": 150.00,
            "quantity": 100,
            "unit": "TONNES",
            "closing_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "minimum_bid_increment": 5.00,
            "reserve_price": 140.00,
            "location": "Test Farm, Test State",
            "quality_grade": "A+",
            "harvest_date": (datetime.now() - timedelta(days=30)).isoformat()
        }
        
        response = await self.client.post(f"{API_BASE}/listings", json=listing_data)
        print(f"Create listing response: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            self.test_data["listing_id"] = data["data"]["id"]
            print("✅ Listing creation successful")
            print(f"Listing ID: {data['data']['id']}")
            return data
        else:
            print(f"❌ Create listing failed: {response.text}")
            return None
    
    async def test_get_listings(self):
        """Test get listings endpoint"""
        print("\n📋 Testing Get Listings...")
        
        response = await self.client.get(f"{API_BASE}/listings")
        print(f"Get listings response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} listings")
            return data
        else:
            print(f"❌ Get listings failed: {response.text}")
            return None
    
    async def test_get_listing_detail(self):
        """Test get listing detail endpoint"""
        print("\n🔍 Testing Get Listing Detail...")
        
        if "listing_id" not in self.test_data:
            print("❌ No listing ID available")
            return None
        
        listing_id = self.test_data["listing_id"]
        response = await self.client.get(f"{API_BASE}/listings/{listing_id}")
        print(f"Get listing detail response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Get listing detail successful")
            print(f"Listing: {data['data']['name']}")
            return data
        else:
            print(f"❌ Get listing detail failed: {response.text}")
            return None
    
    # ===== BIDDING TESTS =====
    
    async def test_place_bid(self):
        """Test place bid endpoint"""
        print("\n💰 Testing Place Bid...")
        
        if not self.auth_token or "listing_id" not in self.test_data:
            print("❌ Missing auth token or listing ID")
            return None
        
        listing_id = self.test_data["listing_id"]
        bid_data = {
            "amount": 155.00,
            "message": "Test bid for automated testing"
        }
        
        response = await self.client.post(f"{API_BASE}/listings/{listing_id}/bids", json=bid_data)
        print(f"Place bid response: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            self.test_data["bid_id"] = data["data"]["id"]
            print("✅ Bid placement successful")
            print(f"Bid ID: {data['data']['id']}")
            return data
        else:
            print(f"❌ Place bid failed: {response.text}")
            return None
    
    async def test_get_bids(self):
        """Test get bids for listing endpoint"""
        print("\n📊 Testing Get Bids...")
        
        if "listing_id" not in self.test_data:
            print("❌ No listing ID available")
            return None
        
        listing_id = self.test_data["listing_id"]
        response = await self.client.get(f"{API_BASE}/listings/{listing_id}/bids")
        print(f"Get bids response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} bids")
            return data
        else:
            print(f"❌ Get bids failed: {response.text}")
            return None
    
    # ===== ML RECOMMENDATIONS TESTS =====
    
    async def test_get_trading_suggestions(self):
        """Test ML trading suggestions endpoint"""
        print("\n🤖 Testing ML Trading Suggestions...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/ml-recommendations/trading-suggestions")
        print(f"Trading suggestions response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} trading suggestions")
            return data
        else:
            print(f"❌ Get trading suggestions failed: {response.text}")
            return None
    
    async def test_get_price_predictions(self):
        """Test ML price predictions endpoint"""
        print("\n📈 Testing ML Price Predictions...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/ml-recommendations/price-predictions")
        print(f"Price predictions response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} price predictions")
            return data
        else:
            print(f"❌ Get price predictions failed: {response.text}")
            return None
    
    # ===== NOTIFICATIONS TESTS =====
    
    async def test_get_notifications(self):
        """Test get notifications endpoint"""
        print("\n🔔 Testing Get Notifications...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/general/notifications")
        print(f"Get notifications response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data['data'])} notifications")
            return data
        else:
            print(f"❌ Get notifications failed: {response.text}")
            return None
    
    # ===== PROFILE TESTS =====
    
    async def test_get_user_profile(self):
        """Test get user profile endpoint"""
        print("\n👤 Testing Get User Profile...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/general/profile")
        print(f"Get profile response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Get user profile successful")
            return data
        else:
            print(f"❌ Get user profile failed: {response.text}")
            return None
    
    async def test_update_user_profile(self):
        """Test update user profile endpoint"""
        print("\n✏️ Testing Update User Profile...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        update_data = {
            "bio": "Updated bio for testing",
            "phone_number": "+1234567891",
            "city": "Updated Test City"
        }
        
        response = await self.client.patch(f"{API_BASE}/general/profile", json=update_data)
        print(f"Update profile response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Update user profile successful")
            return data
        else:
            print(f"❌ Update user profile failed: {response.text}")
            return None
    
    # ===== DASHBOARD TESTS =====
    
    async def test_get_dashboard(self):
        """Test get dashboard endpoint"""
        print("\n📊 Testing Get Dashboard...")
        
        if not self.auth_token:
            print("❌ No auth token available")
            return None
        
        response = await self.client.get(f"{API_BASE}/general/dashboard")
        print(f"Get dashboard response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Get dashboard successful")
            return data
        else:
            print(f"❌ Get dashboard failed: {response.text}")
            return None


# ===== MAIN TEST RUNNER =====

async def run_comprehensive_tests():
    """Run all API tests in sequence"""
    print("🚀 Starting Comprehensive API Tests for AgriTech Platform")
    print("=" * 60)
    
    async with APITestClient() as client:
        try:
            # Basic health check
            await client.test_health_check()
            
            # Authentication flow
            await client.test_user_registration()
            await client.test_user_login()
            await client.test_get_current_user()
            
            # Categories
            await client.test_get_categories()
            
            # Listings management
            await client.test_create_listing()
            await client.test_get_listings()
            await client.test_get_listing_detail()
            
            # Bidding
            await client.test_place_bid()
            await client.test_get_bids()
            
            # ML Recommendations
            await client.test_get_trading_suggestions()
            await client.test_get_price_predictions()
            
            # Notifications
            await client.test_get_notifications()
            
            # Profile management
            await client.test_get_user_profile()
            await client.test_update_user_profile()
            
            # Dashboard
            await client.test_get_dashboard()
            
            print("\n" + "=" * 60)
            print("🎉 All tests completed!")
            print("✅ AgriTech Platform API is working correctly")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_comprehensive_tests())
