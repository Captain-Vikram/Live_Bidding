# 📡 API Documentation

## 🌐 **AgriTech Platform REST API**

Complete API documentation for the AgriTech Smart Bidding Platform. This RESTful API provides endpoints for user management, commodity trading, real-time bidding, and ML-powered recommendations.

---

## 🔗 **Base URL & Interactive Documentation**

**Base URL**: `http://localhost:8000/api/v6`  
**Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)  

---

## 🔐 **Authentication**

### **Authentication Methods**

1. **JWT Bearer Token** (Registered Users)
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

2. **Guest User ID** (Anonymous Users)
```http
guestuserid: 550e8400-e29b-41d4-a716-446655440000
```

### **Getting Authentication Tokens**

**Login Request**:
```http
POST /api/v6/auth/login
Content-Type: application/json

{
  "email": "farmer@agritech.com",
  "password": "securePassword123"
}
```

**Response**:
```json
{
  "message": "Login successful",
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "farmer@agritech.com",
      "first_name": "John",
      "last_name": "Farmer",
      "role": "FARMER",
      "is_verified": true
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

---

## 👥 **Authentication Endpoints**

### **POST /auth/register**
Register a new user account

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "FARMER",
  "terms_agreement": true
}
```

**Response** (201 Created):
```json
{
  "message": "Registration successful. Please verify your email.",
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "newuser@example.com",
    "verification_sent": true
  }
}
```

### **POST /auth/verify-email**
Verify email with OTP

**Request Body**:
```json
{
  "email": "newuser@example.com",
  "otp": 123456
}
```

### **POST /auth/login**
User login

### **POST /auth/refresh-token**
Refresh JWT token

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### **POST /auth/logout**
User logout (requires authentication)

### **POST /auth/forgot-password**
Initiate password reset

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

### **POST /auth/reset-password**
Reset password with OTP

**Request Body**:
```json
{
  "email": "user@example.com",
  "otp": 123456,
  "new_password": "NewSecurePass123"
}
```

---

## 🏠 **Listings & Commodities**

### **GET /listings**
Get all commodity listings with filtering

**Query Parameters**:
- `category_id` (UUID): Filter by category
- `search` (string): Search in name/description
- `min_price` (decimal): Minimum price filter
- `max_price` (decimal): Maximum price filter
- `status` (string): active, closed, all
- `location` (string): Filter by location
- `quality_grade` (string): A, B, C, PREMIUM
- `page` (int): Page number (default: 1)
- `size` (int): Items per page (default: 50)
- `sort` (string): price_asc, price_desc, date_asc, date_desc

**Response**:
```json
{
  "message": "Listings fetched successfully",
  "data": [
    {
      "id": "listing-uuid",
      "name": "Premium Wheat - Grade A",
      "slug": "premium-wheat-grade-a-2025-07-20",
      "description": "High-quality wheat from Maharashtra farms...",
      "category": {
        "id": "category-uuid",
        "name": "Grains",
        "slug": "grains"
      },
      "auctioneer": {
        "id": "user-uuid",
        "name": "John Farmer",
        "rating": 4.8,
        "verified": true
      },
      "price": 125.50,
      "highest_bid": 130.25,
      "bids_count": 15,
      "quantity": 100.0,
      "unit": "TONNES",
      "quality_grade": "A",
      "closing_date": "2025-07-25T18:00:00Z",
      "time_remaining": {
        "days": 5,
        "hours": 8,
        "minutes": 30
      },
      "images": [
        {
          "id": "image-uuid",
          "url": "https://res.cloudinary.com/agritech/image/upload/...",
          "thumbnail": "https://res.cloudinary.com/agritech/image/upload/c_thumb,w_200,h_200/..."
        }
      ],
      "location": "Pune, Maharashtra",
      "harvest_date": "2025-06-15",
      "delivery_terms": "FOB farm gate",
      "payment_terms": "Net 15 days",
      "featured": false,
      "auto_extend": true,
      "reserve_met": true,
      "created_at": "2025-07-20T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 150,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### **GET /listings/{listing_id}**
Get detailed listing information

**Response**:
```json
{
  "message": "Listing details fetched",
  "data": {
    "id": "listing-uuid",
    "name": "Premium Wheat - Grade A",
    // ... (same as above with additional details)
    "detailed_description": "Detailed farming information...",
    "storage_location": "Climate-controlled warehouse",
    "certifications": ["Organic", "FSSAI"],
    "bid_history": [
      {
        "amount": 130.25,
        "bidder": "Anonymous Bidder",
        "bid_time": "2025-07-20T15:30:00Z",
        "is_winning": true
      }
    ],
    "price_history": [
      {
        "date": "2025-07-19",
        "price": 122.00
      }
    ],
    "related_listings": [
      // Similar listings
    ]
  }
}
```

### **POST /listings**
Create a new listing (requires FARMER role)

**Request Body**:
```json
{
  "name": "Premium Wheat - Grade A",
  "description": "High-quality wheat from organic farms",
  "category_id": "category-uuid",
  "price": 125.50,
  "quantity": 100.0,
  "unit": "TONNES",
  "quality_grade": "A",
  "closing_date": "2025-07-25T18:00:00Z",
  "harvest_date": "2025-06-15",
  "storage_location": "Climate-controlled warehouse",
  "delivery_terms": "FOB farm gate",
  "payment_terms": "Net 15 days",
  "min_bid_increment": 1.00,
  "auto_extend": true,
  "featured": false,
  "images": ["image-uuid-1", "image-uuid-2"]
}
```

### **PUT /listings/{listing_id}**
Update listing (owner only)

### **DELETE /listings/{listing_id}**
Delete listing (owner/admin only)

---

## 🎯 **Bidding System**

### **GET /listings/{listing_id}/bids**
Get bid history for a listing

**Response**:
```json
{
  "message": "Bid history fetched",
  "data": [
    {
      "id": "bid-uuid",
      "amount": 130.25,
      "bidder": {
        "id": "user-uuid",
        "name": "Anonymous Bidder",
        "verified": true
      },
      "bid_time": "2025-07-20T15:30:00Z",
      "is_winning": true,
      "auto_bid": false
    }
  ],
  "statistics": {
    "total_bids": 15,
    "unique_bidders": 8,
    "highest_bid": 130.25,
    "average_bid": 127.80
  }
}
```

### **POST /listings/{listing_id}/bids**
Place a bid (requires verified user)

**Request Body**:
```json
{
  "amount": 132.00,
  "auto_bid": false,
  "max_auto_bid": 140.00
}
```

**Response**:
```json
{
  "message": "Bid placed successfully",
  "data": {
    "bid_id": "bid-uuid",
    "amount": 132.00,
    "is_winning": true,
    "previous_highest": 130.25,
    "next_minimum": 133.00,
    "time_remaining": {
      "days": 5,
      "hours": 8,
      "minutes": 28
    }
  }
}
```

### **POST /listings/{listing_id}/auto-bid**
Set up automatic bidding

**Request Body**:
```json
{
  "max_amount": 150.00,
  "increment": 2.00,
  "strategy": "conservative"
}
```

---

## 📂 **Categories**

### **GET /commodities/categories**
Get all commodity categories

**Response**:
```json
{
  "message": "Categories fetched",
  "data": [
    {
      "id": "category-uuid",
      "name": "Grains",
      "slug": "grains",
      "description": "Cereal grains and pulses",
      "image": {
        "url": "https://res.cloudinary.com/agritech/image/upload/..."
      },
      "subcategories": [
        {
          "id": "sub-category-uuid",
          "name": "Wheat",
          "slug": "wheat",
          "listings_count": 25
        }
      ],
      "listings_count": 150,
      "is_active": true
    }
  ]
}
```

---

## 👤 **User Profile & Management**

### **GET /auth/profile**
Get current user profile (requires authentication)

**Response**:
```json
{
  "message": "Profile fetched",
  "data": {
    "user": {
      "id": "user-uuid",
      "email": "farmer@agritech.com",
      "first_name": "John",
      "last_name": "Farmer",
      "role": "FARMER",
      "is_verified": true,
      "is_active": true,
      "avatar": {
        "url": "https://res.cloudinary.com/agritech/image/upload/..."
      },
      "created_at": "2025-01-15T10:00:00Z"
    },
    "profile": {
      "phone_number": "+91-9876543210",
      "address": "Farm Road, Village Name",
      "city": "Pune",
      "state": "Maharashtra",
      "country": "India",
      "postal_code": "411001",
      "date_of_birth": "1985-05-15",
      "company_name": "Green Valley Farms",
      "bio": "Organic farmer with 15 years experience"
    },
    "statistics": {
      "listings_created": 45,
      "successful_sales": 38,
      "total_bids": 127,
      "rating": 4.8,
      "verified_since": "2025-02-01T00:00:00Z"
    }
  }
}
```

### **PUT /auth/profile**
Update user profile

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Farmer",
  "phone_number": "+91-9876543210",
  "address": "Updated Farm Road",
  "city": "Pune",
  "bio": "Updated bio"
}
```

---

## 🔔 **Watchlist**

### **GET /listings/watchlist**
Get user's watchlist

### **POST /listings/watchlist**
Add listing to watchlist

**Request Body**:
```json
{
  "listing_id": "listing-uuid"
}
```

### **DELETE /listings/watchlist/{listing_id}**
Remove from watchlist

---

## 📊 **Price Tracking & Alerts**

### **GET /price-tracking/history**
Get price history for commodities

**Query Parameters**:
- `commodity_slug` (string): Specific commodity
- `location` (string): Market location
- `days` (int): Number of days (default: 30)

**Response**:
```json
{
  "message": "Price history fetched",
  "data": {
    "commodity_slug": "wheat-premium",
    "commodity_name": "Premium Wheat",
    "current_price": 125.50,
    "price_change_24h": 2.30,
    "price_change_percent": 1.87,
    "history": [
      {
        "date": "2025-07-20",
        "price": 125.50,
        "volume": 1500.0,
        "market": "APMC Pune"
      }
    ],
    "statistics": {
      "avg_price_30d": 123.75,
      "min_price_30d": 118.00,
      "max_price_30d": 128.50,
      "volatility": 0.12
    }
  }
}
```

### **POST /price-tracking/alerts**
Create price alert

**Request Body**:
```json
{
  "commodity_slug": "wheat-premium",
  "alert_type": "PRICE_ABOVE",
  "threshold_value": 130.00,
  "notification_methods": {
    "email": true,
    "sms": false,
    "push": true
  }
}
```

### **GET /price-tracking/alerts**
Get user's price alerts

---

## 🤖 **ML Recommendations**

### **GET /ml/recommendations/{commodity_slug}**
Get AI-powered trading recommendations

**Response**:
```json
{
  "message": "Trading recommendation generated",
  "data": {
    "suggestion": "BUY",
    "current_price": 125.50,
    "predicted_price": 135.20,
    "avg_price_30d": 120.30,
    "confidence": 0.85,
    "price_change_pct": 7.72,
    "reason": "Price expected to rise significantly and currently below average",
    "volatility": 0.12,
    "market_position": "ABOVE_AVG",
    "factors": [
      "Seasonal demand increase",
      "Limited supply in region",
      "Historical price patterns"
    ]
  }
}
```

### **GET /ml/predictions/{commodity_slug}**
Get price predictions

**Response**:
```json
{
  "message": "Price predictions generated",
  "data": {
    "commodity_slug": "wheat-premium",
    "predictions": [
      {
        "date": "2025-07-21",
        "predicted_price": 135.20,
        "confidence": 0.85,
        "day_ahead": 1
      },
      {
        "date": "2025-07-22",
        "predicted_price": 137.80,
        "confidence": 0.78,
        "day_ahead": 2
      }
    ],
    "model_info": {
      "model_type": "Prophet + Linear Regression",
      "training_samples": 250,
      "last_trained": "2025-07-20T06:00:00Z",
      "accuracy": 0.82
    }
  }
}
```

---

## 📱 **Mobile & Notifications**

### **POST /mobile/register-device**
Register mobile device for push notifications

**Request Body**:
```json
{
  "device_id": "unique-device-identifier",
  "fcm_token": "firebase-cloud-messaging-token",
  "device_type": "ANDROID",
  "device_model": "Samsung Galaxy S21",
  "os_version": "Android 12",
  "app_version": "1.2.0"
}
```

### **GET /mobile/notifications**
Get in-app notifications

### **PUT /mobile/notification-preferences**
Update notification preferences

**Request Body**:
```json
{
  "email_notifications": true,
  "push_notifications": true,
  "bid_notifications": true,
  "price_alerts": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00"
}
```

---

## 🔄 **Real-time WebSocket**

### **WebSocket Connection**
Connect to real-time updates

**Endpoint**: `ws://localhost:8000/api/v6/realtime/ws/{listing_id}`

**Authentication**: Include JWT token in query parameter
```
ws://localhost:8000/api/v6/realtime/ws/listing-uuid?token=jwt-token
```

**Message Types**:

1. **New Bid**:
```json
{
  "type": "new_bid",
  "data": {
    "listing_id": "listing-uuid",
    "bid_amount": 132.00,
    "bidder": "Anonymous",
    "is_winning": true,
    "time_remaining": "5d 8h 25m"
  }
}
```

2. **Auction Extended**:
```json
{
  "type": "auction_extended",
  "data": {
    "listing_id": "listing-uuid",
    "new_closing_time": "2025-07-25T18:15:00Z",
    "extension_minutes": 15
  }
}
```

3. **Auction Ended**:
```json
{
  "type": "auction_ended",
  "data": {
    "listing_id": "listing-uuid",
    "winning_bid": 145.50,
    "winner": "Anonymous",
    "total_bids": 28
  }
}
```

---

## 📈 **Admin Endpoints**

### **GET /admin/dashboard**
Admin dashboard statistics (requires admin role)

### **GET /admin/users**
Manage users

### **PUT /admin/users/{user_id}/verify**
Verify user KYC

### **GET /admin/listings/pending**
Get pending listings for approval

---

## 🛡️ **Security & Error Handling**

### **Rate Limiting**
- **Standard endpoints**: 100 requests/minute
- **Authentication endpoints**: 10 requests/minute
- **File upload**: 5 uploads/minute

### **HTTP Status Codes**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Server Error |

### **Error Response Format**
```json
{
  "error": "Validation Error",
  "message": "The provided data is invalid",
  "details": {
    "field_name": ["Field is required"]
  },
  "timestamp": "2025-07-20T15:30:00Z",
  "path": "/api/v6/listings"
}
```

---

## 📋 **Request/Response Examples**

### **Pagination Format**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 150,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### **File Upload Response**
```json
{
  "message": "File uploaded successfully",
  "data": {
    "file_id": "file-uuid",
    "url": "https://res.cloudinary.com/agritech/image/upload/v1234567890/sample.jpg",
    "thumbnail": "https://res.cloudinary.com/agritech/image/upload/c_thumb,w_200,h_200/v1234567890/sample.jpg",
    "size": 1024000,
    "format": "jpg"
  }
}
```

---

## 🔧 **Development Tools**

### **API Testing**
- **Swagger UI**: `http://localhost:8000/docs`
- **Postman Collection**: Available in `/docs/postman/`
- **curl Examples**: Available in `/docs/curl-examples/`

### **Authentication Testing**
```bash
# Get access token
curl -X POST "http://localhost:8000/api/v6/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@agritech.com","password":"testpass123"}'

# Use token in requests
curl -X GET "http://localhost:8000/api/v6/listings" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

This comprehensive API documentation provides all endpoints, request/response formats, and examples needed for frontend development integration.
