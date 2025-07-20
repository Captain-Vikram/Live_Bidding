# AgriTech Platform API Documentation

## Overview
Complete API documentation for the AgriTech Smart Bidding Platform with ML-powered recommendations.

**Base URL**: `http://localhost:8000`
**API Version**: `v6.0.0`
**Authentication**: Bearer Token (JWT)

## Authentication
Most endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Response Format
All API responses follow this standard format:
```json
{
  "message": "Success message",
  "data": {
    // Response data
  }
}
```

## Error Responses
Error responses include HTTP status codes and descriptive messages:
```json
{
  "detail": "Error description",
  "error_code": "ERROR_TYPE"
}
```

## Rate Limiting
- 60 requests per minute per IP
- 1000 requests per hour per IP
- Rate limit headers included in responses

---

## Authentication

### POST /api/v1/auth/register

**User Registration**

Register a new user with role-based access (farmer, trader, admin)

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "farmer@agritech.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Farmer",
  "role": "farmer",
  "terms_agreement": true,
  "upi_id": "john@paytm",
  "bank_account": "1234567890123456",
  "ifsc_code": "HDFC0001234"
}
```

**Response**:
```json
{
  "message": "Registration successful",
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "farmer@agritech.com",
      "first_name": "John",
      "last_name": "Farmer",
      "role": "farmer",
      "is_verified": false
    }
  }
}
```

**Error Codes**:
- `400`: Validation error or email already exists
- `422`: Invalid input data format

---

### POST /api/v1/auth/login

**User Login**

Authenticate user and receive access tokens

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "farmer@agritech.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "farmer@agritech.com",
      "role": "farmer",
      "is_verified": true
    }
  }
}
```

**Error Codes**:
- `400`: Invalid credentials
- `429`: Too many login attempts

---

### POST /api/v1/auth/reset-password

**Password Reset Request**

Request password reset via email

**Authentication**: Not required

**Request Body**:
```json
{
  "email": "farmer@agritech.com"
}
```

**Response**:
```json
{
  "message": "Password reset email sent",
  "data": {
    "email_sent": true
  }
}
```

**Error Codes**:
- `404`: Email not found

---

## Commodities

### POST /api/v1/commodities/

**Create Commodity Listing**

Create a new commodity listing for auction

**Authentication**: Required (farmer)

**Request Body**:
```json
{
  "commodity_name": "Premium Basmati Rice",
  "description": "High-quality aged basmati rice from Punjab",
  "quantity_kg": 1000.0,
  "harvest_date": "2025-01-15",
  "min_price": 45.5,
  "closing_date": "2025-08-01T12:00:00Z"
}
```

**Response**:
```json
{
  "message": "Commodity created successfully",
  "data": {
    "id": "987fcdeb-51a2-43d7-b456-426614174000",
    "commodity_name": "Premium Basmati Rice",
    "description": "High-quality aged basmati rice from Punjab",
    "quantity_kg": 1000.0,
    "min_price": 45.5,
    "current_price": 45.5,
    "status": "active",
    "seller_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2025-07-20T10:30:00Z"
  }
}
```

**Error Codes**:
- `400`: Validation error
- `401`: Authentication required
- `403`: Farmer role required

---

### GET /api/v1/commodities/

**Get All Commodities**

Retrieve all active commodity listings with pagination

**Authentication**: Not required

**Response**:
```json
{
  "message": "Commodities retrieved successfully",
  "data": [
    {
      "id": "987fcdeb-51a2-43d7-b456-426614174000",
      "commodity_name": "Premium Basmati Rice",
      "description": "High-quality aged basmati rice",
      "quantity_kg": 1000.0,
      "min_price": 45.5,
      "current_price": 48.75,
      "status": "active",
      "seller": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "first_name": "John",
        "last_name": "Farmer"
      },
      "bids_count": 5,
      "closing_date": "2025-08-01T12:00:00Z"
    }
  ]
}
```

---

## Bidding

### POST /api/v1/bidding/place-bid

**Place Bid**

Place a bid on a commodity listing

**Authentication**: Required (trader)

**Request Body**:
```json
{
  "commodity_listing_id": "987fcdeb-51a2-43d7-b456-426614174000",
  "amount": 50.0
}
```

**Response**:
```json
{
  "message": "Bid placed successfully",
  "data": {
    "id": "456e7890-f12c-34e5-d678-901234567890",
    "commodity_listing_id": "987fcdeb-51a2-43d7-b456-426614174000",
    "bidder_id": "789abc12-3456-78de-f012-345678901234",
    "amount": 50.0,
    "status": "active",
    "created_at": "2025-07-20T14:30:00Z"
  }
}
```

**Error Codes**:
- `400`: Bid amount too low or invalid
- `401`: Authentication required
- `403`: Trader role required or KYC not verified
- `404`: Commodity not found

---

## Price Tracking

### POST /api/v1/price-tracking/alerts

**Create Price Alert**

Set up price alert notification for a commodity

**Authentication**: Required (farmer, trader)

**Request Body**:
```json
{
  "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
  "threshold_price": 45.0,
  "direction": "BELOW",
  "notify_email": true,
  "notify_sms": true
}
```

**Response**:
```json
{
  "message": "Price alert created successfully",
  "data": {
    "id": "alert123-4567-89ab-cdef-012345678901",
    "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
    "user_id": "789abc12-3456-78de-f012-345678901234",
    "threshold_price": 45.0,
    "direction": "BELOW",
    "active": true,
    "created_at": "2025-07-20T15:00:00Z"
  }
}
```

**Error Codes**:
- `400`: Invalid alert parameters
- `401`: Authentication required
- `404`: Commodity not found

---

## ML Recommendations

### GET /api/v6/recommendations/suggestions/{commodity_slug}

**Get ML Trading Recommendation**

Get AI-powered trading recommendation for a specific commodity

**Authentication**: Required (farmer, trader)

**Response**:
```json
{
  "message": "Recommendation generated successfully",
  "data": {
    "commodity_slug": "premium-basmati-rice",
    "suggestion": "BUY",
    "confidence": 0.85,
    "current_price": 48.75,
    "predicted_price": 52.3,
    "avg_price_30d": 46.2,
    "avg_price_7d": 48.1,
    "volatility": 0.12,
    "weekly_trend": 0.025,
    "monthly_trend": 0.055,
    "reasoning": "Price trending upward with strong demand indicators",
    "risk_level": "medium",
    "timestamp": "2025-07-20T16:00:00Z"
  }
}
```

**Error Codes**:
- `400`: Insufficient data for prediction
- `401`: Authentication required
- `404`: Commodity not found

---

### GET /api/v6/recommendations/market-overview

**Get Market Overview**

Get AI-powered market sentiment and trading opportunities

**Authentication**: Required (farmer, trader)

**Response**:
```json
{
  "message": "Market overview generated successfully",
  "data": {
    "market_sentiment": {
      "buy_percentage": 65.0,
      "sell_percentage": 20.0,
      "hold_percentage": 15.0
    },
    "top_buy_opportunities": [
      {
        "commodity_slug": "wheat-premium",
        "suggestion": "BUY",
        "confidence": 0.92,
        "current_price": 28.5,
        "reasoning": "Strong seasonal demand expected"
      }
    ],
    "total_analyzed": 45,
    "timestamp": "2025-07-20T16:00:00Z"
  }
}
```

**Error Codes**:
- `401`: Authentication required

---

## Admin

### PATCH /api/v1/auth/verify-kyc/{user_id}

**Verify User KYC**

Admin endpoint to verify user's KYC status

**Authentication**: Required (admin)

**Request Body**:
```json
{
  "is_verified": true,
  "verification_notes": "All documents verified successfully"
}
```

**Response**:
```json
{
  "message": "KYC verification updated successfully",
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "is_verified": true,
    "verified_at": "2025-07-20T16:30:00Z",
    "verified_by": "admin456-7890-abcd-ef12-345678901234"
  }
}
```

**Error Codes**:
- `401`: Authentication required
- `403`: Admin role required
- `404`: User not found

---

## General

### GET /api/v1/general/health

**Health Check**

Check API health status

**Authentication**: Not required

**Response**:
```json
{
  "message": "AgriTech API is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2025-07-20T17:00:00Z",
    "version": "6.0.0",
    "services": {
      "database": "connected",
      "redis": "connected",
      "ml_engine": "active"
    }
  }
}
```

---

### POST /api/v1/general/upload-image

**Upload Image**

Upload image file for profile or product listing

**Authentication**: Not required

**Request Body**:
```json
null
```

**Response**:
```json
{
  "message": "Image uploaded successfully",
  "data": {
    "file_id": "img12345-6789-abcd-ef01-234567890123",
    "filename": "product_image.jpg",
    "content_type": "image/jpeg",
    "size": 245760
  }
}
```

**Error Codes**:
- `400`: Invalid file type or size
- `413`: File too large

---

## Auctioneer

### POST /api/v1/auctioneer/

**Create General Listing**

Create a general auction listing (non-commodity)

**Authentication**: Required (farmer, trader)

**Request Body**:
```json
{
  "name": "Agricultural Equipment",
  "desc": "High-quality tractor for sale",
  "category": "Equipment",
  "price": 250000.0,
  "closing_date": "2025-08-15T18:00:00Z",
  "file_type": "equipment",
  "image_id": "img12345-6789-abcd-ef01-234567890123"
}
```

**Response**:
```json
{
  "message": "Listing created successfully",
  "data": {
    "id": "listing1-2345-6789-abcd-ef0123456789",
    "name": "Agricultural Equipment",
    "desc": "High-quality tractor for sale",
    "price": 250000.0,
    "status": "active",
    "seller_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2025-07-20T18:00:00Z"
  }
}
```

**Error Codes**:
- `400`: Validation error
- `401`: Authentication required

---

## WebSocket

### WebSocket /ws/bidding/{commodity_id}

**Real-time Bidding Updates**

WebSocket connection for real-time bidding updates

**Authentication**: Required (farmer, trader)

**Request Body**:
```json
{
  "action": "subscribe",
  "data": {
    "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000"
  }
}
```

**Response**:
```json
{
  "type": "bid_update",
  "event": "new_bid",
  "data": {
    "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
    "new_bid": {
      "id": "bid12345-6789-abcd-ef01-234567890123",
      "amount": 52.0,
      "bidder": "Trader John",
      "timestamp": "2025-07-20T18:30:00Z"
    }
  }
}
```

**Error Codes**:
- `401`: Authentication required
- `404`: Commodity not found

---

## Mobile

### POST /mobile/register-device

**Register Mobile Device**

Register mobile device for push notifications

**Authentication**: Required (farmer, trader)

**Request Body**:
```json
{
  "device_token": "dGVzdF9kZXZpY2VfdG9rZW4=",
  "device_type": "android",
  "app_version": "1.0.0",
  "device_name": "Samsung Galaxy S21"
}
```

**Response**:
```json
{
  "message": "Device registered successfully",
  "data": {
    "device_id": "device12-3456-7890-abcd-ef0123456789",
    "device_token": "dGVzdF9kZXZpY2VfdG9rZW4=",
    "device_type": "android",
    "registered_at": "2025-07-20T19:00:00Z"
  }
}
```

**Error Codes**:
- `400`: Invalid device data
- `401`: Authentication required

---

## Usage Examples

### Complete User Journey

#### 1. User Registration
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Farmer",
    "role": "farmer",
    "terms_agreement": true,
    "upi_id": "john@paytm",
    "bank_account": "1234567890123456",
    "ifsc_code": "HDFC0001234"
  }'
```

#### 2. User Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePass123!"
  }'
```

#### 3. Create Commodity Listing
```bash
curl -X POST http://localhost:8000/api/v1/commodities/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "commodity_name": "Premium Wheat",
    "description": "High quality wheat",
    "quantity_kg": 1000.0,
    "harvest_date": "2025-01-15",
    "min_price": 25.50,
    "closing_date": "2025-08-01T12:00:00Z"
  }'
```

#### 4. Place Bid
```bash
curl -X POST http://localhost:8000/api/v1/bidding/place-bid \
  -H "Authorization: Bearer <trader_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "commodity_listing_id": "commodity_id_here",
    "amount": 30.00
  }'
```

#### 5. Get ML Recommendation
```bash
curl -X GET http://localhost:8000/api/v6/recommendations/suggestions/wheat-premium \
  -H "Authorization: Bearer <your_token>"
```

---

## Security

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Rate Limiting
- 60 requests per minute per IP
- 1000 requests per hour per IP
- 5 failed login attempts result in 30-minute lockout

### Data Protection
- All sensitive data encrypted at rest
- HTTPS required in production
- JWT tokens expire after 24 hours
- Audit logging for all critical operations

### KYC Verification
- Required for bidding functionality
- Admin verification process
- Bank account and UPI ID validation
- Document upload support

---

## Changelog

### Version 6.0.0 (Current)
- ✅ ML-powered trading recommendations
- ✅ Advanced price tracking and alerts
- ✅ Real-time bidding with WebSocket
- ✅ Enhanced security with audit logging
- ✅ Mobile device registration
- ✅ Image upload for profiles and listings
- ✅ Email/SMS notification system
- ✅ Comprehensive API testing suite

### Version 5.0.0
- ✅ Price history tracking
- ✅ Alert subscription system
- ✅ On-site notifications
- ✅ Enhanced user roles

### Version 4.0.0
- ✅ Real-time bidding system
- ✅ WebSocket implementation
- ✅ Mobile API endpoints

### Version 3.0.0
- ✅ KYC verification system
- ✅ Admin management tools
- ✅ Enhanced security

### Version 2.0.0
- ✅ Commodity bidding system
- ✅ User authentication
- ✅ Basic marketplace features

### Version 1.0.0
- ✅ Initial API implementation
- ✅ User registration/login
- ✅ Basic commodity listings

---

*Last updated: July 20, 2025*
*API Version: 1.0.0*
*Documentation generated automatically*
