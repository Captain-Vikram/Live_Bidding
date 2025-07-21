# Frontend Testing Guide - AgriTech Platform API Communication

## 🔧 Pre-Flight Checklist

Before starting your frontend development, ensure the backend API is properly running and accessible.

### 1. **Backend Service Status Check**
```bash
# Check if all Docker containers are running
docker-compose ps

# Expected output: All services should show "Up" status
# - bidout-auction-v6-api-1     (API Server)
# - bidout-auction-v6-db-1      (PostgreSQL Database) 
# - bidout-auction-v6-redis-1   (Redis Cache)
# - pgadmin                     (Database Admin)
```

### 2. **API Base Configuration**
```javascript
// Frontend API configuration
const API_CONFIG = {
  BASE_URL: "http://127.0.0.1:8000",
  API_VERSION: "/api/v6",
  TIMEOUT: 10000,
  HEADERS: {
    "Content-Type": "application/json",
    "Accept": "application/json"
  }
};

// Full API base URL
const API_BASE = `${API_CONFIG.BASE_URL}${API_CONFIG.API_VERSION}`;
```

## 🧪 Essential Frontend Tests

### **Test 1: API Health Check**
```javascript
// Test basic API connectivity
async function testAPIHealth() {
  try {
    const response = await fetch('http://127.0.0.1:8000/');
    const data = await response.json();
    
    console.log('✅ API Health:', data);
    // Expected: {"message":"Welcome to AgriTech Platform API","version":"6.0.0","status":"running"}
    
    return response.ok && data.status === "running";
  } catch (error) {
    console.error('❌ API Health Check Failed:', error);
    return false;
  }
}
```

### **Test 2: CORS Configuration**
```javascript
// Test CORS headers for frontend communication
async function testCORS() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/v6/general/site-detail', {
      method: 'GET',
      headers: {
        'Origin': 'http://localhost:3000', // Your frontend URL
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ CORS Test:', response.status);
    return response.ok;
  } catch (error) {
    console.error('❌ CORS Test Failed:', error);
    return false;
  }
}
```

### **Test 3: General Endpoints (No Auth Required)**
```javascript
// Test public endpoints
async function testGeneralEndpoints() {
  const tests = [
    {
      name: 'Site Details',
      url: '/api/v6/general/site-detail',
      method: 'GET',
      expectedFields: ['name', 'email', 'phone', 'address']
    },
    {
      name: 'Reviews',
      url: '/api/v6/general/reviews', 
      method: 'GET',
      expectedFields: ['reviewer', 'text']
    },
    {
      name: 'Newsletter Subscription',
      url: '/api/v6/general/subscribe',
      method: 'POST',
      body: { email: 'test@frontend.com' },
      expectedStatus: 201
    }
  ];

  for (const test of tests) {
    try {
      const options = {
        method: test.method,
        headers: { 'Content-Type': 'application/json' }
      };
      
      if (test.body) {
        options.body = JSON.stringify(test.body);
      }
      
      const response = await fetch(`http://127.0.0.1:8000${test.url}`, options);
      const data = await response.json();
      
      console.log(`✅ ${test.name}:`, data.status === 'success');
    } catch (error) {
      console.error(`❌ ${test.name} Failed:`, error);
    }
  }
}
```

### **Test 4: Authentication Flow**
```javascript
// Test complete authentication workflow
async function testAuthentication() {
  const credentials = {
    admin: { email: 'admin@agritech.com', password: 'admin123' },
    seller: { email: 'seller@agritech.com', password: 'seller123' },
    reviewer: { email: 'reviewer@agritech.com', password: 'reviewer123' }
  };

  for (const [role, creds] of Object.entries(credentials)) {
    try {
      // Test login
      const loginResponse = await fetch('http://127.0.0.1:8000/api/v6/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds)
      });
      
      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        const token = loginData.data.access;
        
        console.log(`✅ ${role} Login:`, loginData.status === 'success');
        
        // Test logout
        const logoutResponse = await fetch('http://127.0.0.1:8000/api/v6/auth/logout', {
          method: 'GET',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json' 
          }
        });
        
        console.log(`✅ ${role} Logout:`, logoutResponse.ok);
      }
    } catch (error) {
      console.error(`❌ ${role} Auth Failed:`, error);
    }
  }
}
```

### **Test 5: Protected Endpoints**
```javascript
// Test authenticated endpoints
async function testProtectedEndpoints() {
  // First login to get token
  const loginResponse = await fetch('http://127.0.0.1:8000/api/v6/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'admin@agritech.com', password: 'admin123' })
  });
  
  if (!loginResponse.ok) {
    console.error('❌ Cannot test protected endpoints - login failed');
    return;
  }
  
  const { data: { access: token } } = await loginResponse.json();
  
  const protectedTests = [
    '/api/v6/listings/all',
    '/api/v6/commodities/all',
    '/api/v6/admin/users',
    '/api/v6/seller/dashboard'
  ];
  
  for (const endpoint of protectedTests) {
    try {
      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json' 
        }
      });
      
      console.log(`✅ ${endpoint}:`, response.ok);
    } catch (error) {
      console.error(`❌ ${endpoint} Failed:`, error);
    }
  }
}
```

### **Test 6: WebSocket Connection**
```javascript
// Test real-time WebSocket connectivity
async function testWebSocket() {
  try {
    const ws = new WebSocket('ws://127.0.0.1:8000/realtime/ws');
    
    ws.onopen = () => {
      console.log('✅ WebSocket Connected');
      ws.send(JSON.stringify({ type: 'ping' }));
    };
    
    ws.onmessage = (event) => {
      console.log('✅ WebSocket Message:', event.data);
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket Error:', error);
    };
    
    // Close after 5 seconds
    setTimeout(() => ws.close(), 5000);
  } catch (error) {
    console.error('❌ WebSocket Test Failed:', error);
  }
}
```

## 📋 Complete Frontend Test Suite

```javascript
// Run all tests sequentially
async function runAllTests() {
  console.log('🚀 Starting Frontend API Communication Tests...\n');
  
  const tests = [
    { name: 'API Health Check', fn: testAPIHealth },
    { name: 'CORS Configuration', fn: testCORS },
    { name: 'General Endpoints', fn: testGeneralEndpoints },
    { name: 'Authentication Flow', fn: testAuthentication },
    { name: 'Protected Endpoints', fn: testProtectedEndpoints },
    { name: 'WebSocket Connection', fn: testWebSocket }
  ];
  
  for (const test of tests) {
    console.log(`\n📝 Running: ${test.name}`);
    try {
      await test.fn();
      console.log(`✅ ${test.name} completed`);
    } catch (error) {
      console.error(`❌ ${test.name} failed:`, error);
    }
  }
  
  console.log('\n🎉 All tests completed!');
}

// Execute tests
runAllTests();
```

## 🛠️ Frontend Setup Requirements

### **1. Environment Variables**
```env
# Frontend .env file
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_API_VERSION=/api/v6
REACT_APP_WS_URL=ws://127.0.0.1:8000
```

### **2. API Client Setup**
```javascript
// api.js - Frontend API client
class AgriTechAPI {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL;
    this.apiVersion = process.env.REACT_APP_API_VERSION;
    this.token = localStorage.getItem('access_token');
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${this.apiVersion}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` })
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  }
  
  // Auth methods
  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    
    if (data.status === 'success') {
      this.token = data.data.access;
      localStorage.setItem('access_token', this.token);
      localStorage.setItem('refresh_token', data.data.refresh);
    }
    
    return data;
  }
  
  async logout() {
    await this.request('/auth/logout');
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
  
  // General methods
  async getSiteDetails() {
    return this.request('/general/site-detail');
  }
  
  async getReviews() {
    return this.request('/general/reviews');
  }
  
  async subscribe(email) {
    return this.request('/general/subscribe', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }
}

// Export singleton instance
export const api = new AgriTechAPI();
```

### **3. Error Handling**
```javascript
// errorHandler.js
export function handleAPIError(error) {
  if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
    return 'Connection error. Please check if the backend server is running.';
  }
  
  if (error.message.includes('401')) {
    return 'Authentication failed. Please login again.';
  }
  
  if (error.message.includes('403')) {
    return 'Access denied. You don\'t have permission for this action.';
  }
  
  if (error.message.includes('404')) {
    return 'Resource not found.';
  }
  
  if (error.message.includes('500')) {
    return 'Server error. Please try again later.';
  }
  
  return error.message || 'An unexpected error occurred.';
}
```

## 🔍 Troubleshooting Common Issues

### **Issue 1: CORS Errors**
```javascript
// If you get CORS errors, verify:
// 1. Backend CORS settings include your frontend URL
// 2. Use correct headers in requests
// 3. Check browser developer tools for specific CORS errors
```

### **Issue 2: Authentication Token Expiry**
```javascript
// Implement token refresh logic
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return false;
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/v6/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  
  return false;
}
```

### **Issue 3: Network Connectivity**
```javascript
// Check backend availability
async function checkBackendHealth() {
  try {
    const response = await fetch('http://127.0.0.1:8000/', { timeout: 5000 });
    return response.ok;
  } catch (error) {
    console.error('Backend is not accessible:', error);
    alert('Backend server is not running. Please start the Docker containers.');
    return false;
  }
}
```

## 📊 Expected Test Results

When running the frontend tests, you should see:

✅ **API Health Check**: Status "running", version "6.0.0"
✅ **CORS Configuration**: No CORS errors
✅ **General Endpoints**: Site details, reviews, subscription working
✅ **Authentication Flow**: Login/logout for all user types
✅ **Protected Endpoints**: Authorized access to restricted routes
✅ **WebSocket Connection**: Real-time communication established

If any test fails, check:
1. Docker containers are running (`docker-compose ps`)
2. Database is initialized with test data
3. Network connectivity between frontend and backend
4. CORS configuration allows your frontend domain

## 🚀 Ready to Develop!

Once all tests pass, your frontend can successfully communicate with the AgriTech Platform API. You can now proceed with building your React/Vue/Angular application with confidence that the backend integration will work smoothly.
