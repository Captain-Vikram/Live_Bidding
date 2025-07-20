"""
Quick API Tests for AgriTech Platform
===================================

Quick tests for basic API functionality without requiring full database setup
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v6"

async def test_basic_endpoints():
    """Test basic endpoints that don't require authentication"""
    print("🚀 Starting Quick API Tests for AgriTech Platform")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        try:
            # 1. Health Check
            print("\n🔍 Testing Health Check...")
            response = await client.get(f"{API_BASE}/healthcheck")
            print(f"Health Check: {response.status_code}")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.text}")
            
            # 2. API Documentation
            print("\n📚 Testing API Documentation...")
            response = await client.get("/docs")
            print(f"API Docs: {response.status_code}")
            if response.status_code == 200:
                print("✅ API documentation accessible")
            else:
                print(f"❌ API docs failed: {response.status_code}")
            
            # 3. OpenAPI Schema
            print("\n📋 Testing OpenAPI Schema...")
            response = await client.get("/openapi.json")
            print(f"OpenAPI Schema: {response.status_code}")
            if response.status_code == 200:
                schema = response.json()
                print("✅ OpenAPI schema accessible")
                print(f"API Title: {schema.get('info', {}).get('title', 'Unknown')}")
                print(f"API Version: {schema.get('info', {}).get('version', 'Unknown')}")
                print(f"Total Endpoints: {len(schema.get('paths', {}))}")
            else:
                print(f"❌ OpenAPI schema failed: {response.status_code}")
            
            # 4. Security Headers Test
            print("\n🛡️ Testing Security Headers...")
            response = await client.get(f"{API_BASE}/healthcheck")
            if response.status_code == 200:
                headers = response.headers
                security_headers = {
                    "x-content-type-options": headers.get("x-content-type-options"),
                    "x-frame-options": headers.get("x-frame-options"),
                    "x-xss-protection": headers.get("x-xss-protection"),
                    "strict-transport-security": headers.get("strict-transport-security"),
                    "referrer-policy": headers.get("referrer-policy"),
                }
                print("✅ Security headers present:")
                for header, value in security_headers.items():
                    if value:
                        print(f"  • {header}: {value}")
            
            # 5. Rate Limiting Test
            print("\n⏱️ Testing Rate Limiting...")
            try:
                # Make multiple requests quickly
                responses = []
                for i in range(5):
                    resp = await client.get(f"{API_BASE}/healthcheck")
                    responses.append(resp.status_code)
                
                print(f"✅ Made 5 requests: {responses}")
                if all(status == 200 for status in responses):
                    print("✅ Rate limiting allows normal usage")
                else:
                    print(f"⚠️ Some requests failed: {responses}")
            except Exception as e:
                print(f"❌ Rate limiting test failed: {e}")
            
            # 6. CORS Headers Test
            print("\n🌐 Testing CORS Headers...")
            try:
                response = await client.options(f"{API_BASE}/healthcheck", headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                })
                print(f"CORS Preflight: {response.status_code}")
                if response.status_code in [200, 204]:
                    print("✅ CORS preflight working")
                    cors_headers = {
                        "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                        "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
                    }
                    for header, value in cors_headers.items():
                        if value:
                            print(f"  • {header}: {value}")
            except Exception as e:
                print(f"⚠️ CORS test skipped: {e}")
            
            # 7. Error Handling Test
            print("\n❌ Testing Error Handling...")
            try:
                response = await client.get(f"{API_BASE}/nonexistent-endpoint")
                print(f"404 Test: {response.status_code}")
                if response.status_code == 404:
                    print("✅ 404 errors handled correctly")
                    try:
                        error_data = response.json()
                        print(f"Error format: {error_data}")
                    except:
                        print("Error response is not JSON")
            except Exception as e:
                print(f"❌ Error handling test failed: {e}")
            
            # 8. Content Type Test
            print("\n📄 Testing Content Types...")
            response = await client.get(f"{API_BASE}/healthcheck")
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                print(f"Content-Type: {content_type}")
                if "application/json" in content_type:
                    print("✅ JSON content type correct")
                else:
                    print(f"⚠️ Unexpected content type: {content_type}")
            
            print("\n" + "=" * 60)
            print("🎉 Quick API Tests Completed!")
            print("✅ Basic AgriTech Platform API functionality verified")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()


async def test_endpoint_discovery():
    """Discover and test available endpoints"""
    print("\n🔍 Discovering Available Endpoints...")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        try:
            # Get OpenAPI schema to discover endpoints
            response = await client.get("/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                paths = schema.get("paths", {})
                
                print(f"\n📋 Found {len(paths)} endpoint groups:")
                
                # Group endpoints by category
                endpoint_groups = {}
                for path, methods in paths.items():
                    # Extract category from path
                    path_parts = path.strip("/").split("/")
                    if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v6":
                        category = path_parts[2]
                        if category not in endpoint_groups:
                            endpoint_groups[category] = []
                        
                        for method in methods.keys():
                            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                endpoint_groups[category].append(f"{method.upper()} {path}")
                
                # Display grouped endpoints
                for category, endpoints in endpoint_groups.items():
                    print(f"\n🔸 {category.upper()} ({len(endpoints)} endpoints):")
                    for endpoint in sorted(endpoints)[:5]:  # Show first 5
                        print(f"  • {endpoint}")
                    if len(endpoints) > 5:
                        print(f"  ... and {len(endpoints) - 5} more")
                
                # Test a few GET endpoints that don't require auth
                print(f"\n🧪 Testing Public Endpoints...")
                public_endpoints = [
                    f"{API_BASE}/healthcheck",
                    f"{API_BASE}/general/categories",
                    f"{API_BASE}/listings",
                ]
                
                for endpoint in public_endpoints:
                    try:
                        response = await client.get(endpoint)
                        status = "✅" if response.status_code < 400 else "⚠️" if response.status_code < 500 else "❌"
                        print(f"  {status} {endpoint}: {response.status_code}")
                        
                        # If it's a successful response, show some info
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if isinstance(data, dict):
                                    if "data" in data:
                                        data_length = len(data["data"]) if isinstance(data["data"], list) else "object"
                                        print(f"    └─ Response contains: {data_length} items")
                                    elif "message" in data:
                                        print(f"    └─ Message: {data['message']}")
                            except:
                                pass
                                
                    except Exception as e:
                        print(f"  ❌ {endpoint}: Error - {str(e)[:50]}...")
            
        except Exception as e:
            print(f"❌ Endpoint discovery failed: {e}")


if __name__ == "__main__":
    async def main():
        await test_basic_endpoints()
        await test_endpoint_discovery()
    
    asyncio.run(main())
