# 🌾 AgriTech Platform - Complete API Documentation v6.0.0

## 📋 Overview
**Base URL**: `http://localhost:8000`  
**API Version**: `v6.0.0`  
**Authentication**: Bearer JWT Token  
**CORS**: Enabled for `localhost:3000`, `localhost:3001`, `localhost:8080`  
**Rate Limiting**: 1000 requests/hour per IP

## 🔐 Authentication Required
Most endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

## 📊 Response Format
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { /* response data */ }
}
```

---

## 🎯 API Endpoints

### 🔑 Authentication (`/api/v6/auth`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `POST` | `/register` | User Registration | ❌ | - |
| `POST` | `/login` | User Login | ❌ | - |
| `GET` | `/logout` | User Logout | ✅ | All |
| `POST` | `/refresh` | Refresh Tokens | ❌ | - |
| `POST` | `/request-otp` | Request OTP | ❌ | - |
| `POST` | `/verify-otp` | Verify OTP | ❌ | - |
| `POST` | `/set-new-password` | Reset Password | ❌ | - |
| `POST` | `/verify-kyc/{user_id}` | Verify User KYC | ✅ | ADMIN |

**Registration Request**:
```json
{
  "first_name": "John",
  "last_name": "Farmer",
  "email": "farmer@example.com",
  "password": "SecurePass123!",
  "role": "FARMER",
  "terms_agreement": true,
  "phone_number": "1234567890"
}
```

**Login Request**:
```json
{
  "email": "farmer@example.com",
  "password": "SecurePass123!"
}
```

---

### 🏪 Listings Management (`/api/v6/listings`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/` | Get All Listings | ❌ | - |
| `GET` | `/{listing_id}` | Get Listing Details | ❌ | - |
| `POST` | `/watchlist` | Add to Watchlist | ❌ | User/Guest |
| `DELETE` | `/watchlist/{id}` | Remove from Watchlist | ❌ | User/Guest |
| `GET` | `/categories` | Get All Categories | ❌ | - |
| `GET` | `/categories/{slug}` | Get Category Listings | ❌ | - |
| `POST` | `/bid` | Place Bid | ✅ | TRADER |

**Create Bid Request**:
```json
{
  "listing_id": "uuid",
  "amount": 150.50
}
```

---

### 👨‍🌾 Seller/Farmer (`/api/v6/seller`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/` | Get Profile | ✅ | FARMER |
| `PUT` | `/` | Update Profile | ✅ | FARMER |
| `GET` | `/listings` | Get User Listings | ✅ | FARMER |
| `POST` | `/listings` | Create Listing | ✅ | FARMER |
| `PUT` | `/listings/{id}` | Update Listing | ✅ | FARMER |
| `DELETE` | `/listings/{id}` | Delete Listing | ✅ | FARMER |

**Create Listing Request**:
```json
{
  "name": "Premium Wheat",
  "desc": "High quality wheat from Punjab",
  "category": "grains",
  "price": 25.50,
  "closing_date": "2025-08-15T18:00:00Z",
  "file_type": "image",
  "quantity": 1000,
  "unit": "KG"
}
```

---

### 🏛️ Auctioneer (`/api/v6/auctioneer`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/` | Get Profile | ✅ | AUCTIONEER |
| `PUT` | `/` | Update Profile | ✅ | AUCTIONEER |
| `GET` | `/listings` | Get Managed Listings | ✅ | AUCTIONEER |
| `POST` | `/listings` | Create General Listing | ✅ | AUCTIONEER |

---

### 🎯 Bidding System (`/api/v6/bidding`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `POST` | `/place-bid` | Place Bid | ✅ | TRADER |
| `GET` | `/my-bids` | Get User Bids | ✅ | TRADER |
| `GET` | `/listing/{id}/bids` | Get Listing Bids | ❌ | - |
| `POST` | `/auto-bid` | Set Auto Bidding | ✅ | TRADER |

---

### 🌾 Commodities (`/api/v6/commodities`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/` | Get Approved Commodities | ❌ | - |
| `GET` | `/{id}` | Get Commodity Details | ❌ | - |
| `POST` | `/` | Create Commodity | ✅ | FARMER |
| `PUT` | `/{id}` | Update Commodity | ✅ | FARMER |
| `DELETE` | `/{id}` | Delete Commodity | ✅ | FARMER |

**Create Commodity Request**:
```json
{
  "commodity_name": "Basmati Rice",
  "description": "Premium quality basmati rice",
  "quantity_kg": 500.0,
  "min_price": 45.00,
  "harvest_date": "2025-01-15",
  "closing_date": "2025-08-01T12:00:00Z",
  "quality_grade": "A",
  "storage_location": "Punjab"
}
```

---

### 👑 Admin Panel (`/api/v6/admin`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/users` | List All Users | ✅ | ADMIN |
| `GET` | `/users/{id}` | Get User Details | ✅ | ADMIN |
| `PATCH` | `/users/{id}/verification` | Update User Verification | ✅ | ADMIN |
| `DELETE` | `/users/{id}` | Delete User | ✅ | ADMIN |
| `GET` | `/pending-commodities/` | Get Pending Approvals | ✅ | ADMIN |
| `POST` | `/approve-commodity/{id}` | Approve/Reject Commodity | ✅ | ADMIN |
| `GET` | `/active-bids` | Get Active Bids Stats | ✅ | ADMIN |
| `GET` | `/commodities/count` | Get Commodities Stats | ✅ | ADMIN |
| `GET` | `/stats/platform` | Get Platform Stats | ✅ | ADMIN |

---

### 📊 Price Tracking (`/api/v6/price-tracking`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/history/{commodity}` | Get Price History | ❌ | - |
| `POST` | `/alerts` | Create Price Alert | ✅ | All |
| `GET` | `/alerts` | Get User Alerts | ✅ | All |
| `PUT` | `/alerts/{id}` | Update Alert | ✅ | All |
| `DELETE` | `/alerts/{id}` | Delete Alert | ✅ | All |
| `GET` | `/statistics/{commodity}` | Get Price Statistics | ❌ | - |
| `GET` | `/trending` | Get Trending Commodities | ❌ | - |
| `GET` | `/dashboard` | Get Dashboard Summary | ✅ | All |
| `GET` | `/notifications` | Get Notifications | ✅ | All |
| `POST` | `/notifications/mark-read` | Mark Notifications Read | ✅ | All |

**Create Alert Request**:
```json
{
  "commodity_slug": "wheat-premium",
  "threshold_price": 30.00,
  "direction": "BELOW",
  "notify_email": true,
  "notify_sms": false
}
```

---

### 🤖 ML Recommendations (`/api/v6/ml`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/suggestions/{commodity_slug}` | Get AI Trading Recommendation | ✅ | All |
| `GET` | `/market-overview` | Get Market Overview | ✅ | All |
| `GET` | `/price-prediction/{commodity}` | Get Price Prediction | ✅ | All |
| `POST` | `/feedback` | Submit ML Feedback | ✅ | All |

**AI Recommendation Response**:
```json
{
  "suggestion": "BUY",
  "confidence": 0.85,
  "current_price": 48.75,
  "predicted_price": 52.30,
  "reasoning": "Strong upward trend with high demand",
  "risk_level": "medium"
}
```

---

### 📱 Mobile & Notifications (`/api/v6/mobile`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `POST` | `/register-device` | Register Mobile Device | ✅ | All |
| `GET` | `/devices` | Get User Devices | ✅ | All |
| `DELETE` | `/devices/{id}` | Unregister Device | ✅ | All |
| `POST` | `/push-notification` | Send Push Notification | ✅ | ADMIN |
| `GET` | `/notification-history` | Get Notification History | ✅ | All |
| `POST` | `/notification-preferences` | Update Preferences | ✅ | All |
| `POST` | `/activity` | Log User Activity | ✅ | All |
| `GET` | `/activity/summary` | Get Activity Summary | ✅ | All |
| `POST` | `/location` | Update User Location | ✅ | All |
| `GET` | `/locations` | Get User Locations | ✅ | All |

---

### 🌐 General (`/api/v6/general`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/site-detail` | Get Site Details | ❌ | - |
| `POST` | `/subscribe` | Newsletter Subscribe | ❌ | - |
| `GET` | `/reviews` | Get Platform Reviews | ❌ | - |
| `POST` | `/upload-image` | Upload Image | ❌ | - |

---

### ⚡ Real-time (`/api/v6/realtime`)

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `WebSocket` | `/ws` | Basic WebSocket Test | ❌ | - |
| `WebSocket` | `/ws/auction/{commodity_id}` | Real-time Auction Updates | ✅ | All |

**WebSocket Message Format**:
```json
{
  "type": "bid_update",
  "event": "new_bid",
  "data": {
    "commodity_id": "uuid",
    "new_bid": {
      "amount": 155.50,
      "bidder": "John Trader",
      "timestamp": "2025-08-02T12:30:00Z"
    }
  }
}
```

---

### 🔍 Health & Monitoring

| Method | Endpoint | Summary | Auth | Roles |
|--------|----------|---------|------|-------|
| `GET` | `/` | Root API Info | ❌ | - |
| `GET` | `/api/v6/healthcheck` | API Health Check | ❌ | - |
| `GET` | `/api/v6/redis-health` | Redis Health Check | ❌ | - |
| `GET` | `/docs` | API Documentation | ❌ | - |
| `GET` | `/openapi.json` | OpenAPI Schema | ❌ | - |

---

## 🔒 Security Features

### Rate Limiting
- **1000 requests/hour** per IP address
- **60 requests/minute** per IP address
- Automatic blocking on abuse detection

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HTTPS)

### Data Protection
- JWT tokens expire in 24 hours
- Password hashing with bcrypt
- Input validation and sanitization
- SQL injection protection

### Audit Logging
- All API requests logged
- Security events tracked
- Failed login attempts monitored

---

## 🎯 User Roles & Permissions

### FARMER
- ✅ Create/manage commodity listings
- ✅ View all listings and bids
- ✅ Access price tracking and alerts
- ✅ Use ML recommendations

### TRADER  
- ✅ Place bids on commodities
- ✅ View all listings
- ✅ Manage watchlist
- ✅ Access price tracking and alerts
- ✅ Use ML recommendations

### AUCTIONEER
- ✅ Create general auction listings
- ✅ Manage auctions
- ✅ View bidding activity

### ADMIN
- ✅ Full platform access
- ✅ User management
- ✅ Commodity approval
- ✅ Platform statistics
- ✅ System configuration

---

## 🚀 Quick Start Examples

### 1. User Registration & Login
```bash
# Register
curl -X POST http://localhost:8000/api/v6/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Farmer", 
    "email": "farmer@example.com",
    "password": "SecurePass123!",
    "role": "FARMER",
    "terms_agreement": true
  }'

# Login  
curl -X POST http://localhost:8000/api/v6/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePass123!"
  }'
```

### 2. Create Commodity Listing
```bash
curl -X POST http://localhost:8000/api/v6/seller/listings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Wheat",
    "desc": "High quality wheat from Punjab",
    "category": "grains",
    "price": 25.50,
    "closing_date": "2025-08-15T18:00:00Z"
  }'
```

### 3. Place Bid
```bash
curl -X POST http://localhost:8000/api/v6/listings/bid \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "commodity-uuid",
    "amount": 30.00
  }'
```

### 4. Get ML Recommendation
```bash
curl -X GET http://localhost:8000/api/v6/ml/suggestions/wheat-premium \
  -H "Authorization: Bearer <token>"
```

---

## 📈 Error Codes

| Code | Description | Example |
|------|-------------|---------|
| `200` | Success | Operation completed |
| `201` | Created | Resource created |
| `400` | Bad Request | Invalid input data |
| `401` | Unauthorized | Invalid/missing token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `422` | Validation Error | Schema validation failed |
| `429` | Rate Limited | Too many requests |
| `500` | Server Error | Internal server error |

---

## 🔄 Changelog

### v6.0.0 (Current)
- ✅ ML-powered trading recommendations
- ✅ Advanced price tracking and alerts  
- ✅ Real-time bidding with WebSocket
- ✅ Mobile device management
- ✅ Enhanced security with audit logging
- ✅ Admin management dashboard
- ✅ Comprehensive API testing

### v5.0.0
- ✅ Price history tracking
- ✅ Alert subscription system
- ✅ Enhanced notifications

### v4.0.0  
- ✅ Real-time bidding system
- ✅ WebSocket implementation

---

*Last Updated: August 2, 2025*  
*API Version: 6.0.0*  
*Total Endpoints: 75+*
