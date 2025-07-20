"""
Complete API Documentation Generator
===================================

Generates comprehensive documentation for all API endpoints including:
- Endpoint descriptions
- Request/response schemas
- Authentication requirements
- Error codes
- Usage examples
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class APIEndpoint:
    """API Endpoint documentation structure"""
    method: str
    path: str
    summary: str
    description: str
    tags: List[str]
    auth_required: bool
    required_roles: List[str]
    request_schema: Optional[Dict]
    response_schema: Dict
    error_codes: List[Dict]
    example_request: Optional[Dict]
    example_response: Dict


class APIDocumentationGenerator:
    """
    Complete API documentation generator for AgriTech Platform
    """
    
    def __init__(self):
        self.endpoints = []
        self.generate_all_endpoints()
    
    def generate_all_endpoints(self):
        """Generate documentation for all API endpoints"""
        
        # Authentication Endpoints
        self.add_auth_endpoints()
        
        # Commodity Management Endpoints
        self.add_commodity_endpoints()
        
        # Bidding System Endpoints
        self.add_bidding_endpoints()
        
        # Price Tracking Endpoints
        self.add_price_tracking_endpoints()
        
        # ML Recommendations Endpoints
        self.add_ml_recommendation_endpoints()
        
        # Admin Endpoints
        self.add_admin_endpoints()
        
        # General Utility Endpoints
        self.add_general_endpoints()
        
        # Auctioneer Endpoints
        self.add_auctioneer_endpoints()
        
        # WebSocket Endpoints
        self.add_websocket_endpoints()
        
        # Mobile & Notification Endpoints
        self.add_mobile_endpoints()
    
    def add_auth_endpoints(self):
        """Authentication and authorization endpoints"""
        
        # User Registration
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/auth/register",
            summary="User Registration",
            description="Register a new user with role-based access (farmer, trader, admin)",
            tags=["Authentication"],
            auth_required=False,
            required_roles=[],
            request_schema={
                "type": "object",
                "required": ["email", "password", "first_name", "last_name", "role", "terms_agreement"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string", "minLength": 8},
                    "first_name": {"type": "string", "maxLength": 50},
                    "last_name": {"type": "string", "maxLength": 50},
                    "role": {"type": "string", "enum": ["farmer", "trader", "admin"]},
                    "terms_agreement": {"type": "boolean"},
                    "upi_id": {"type": "string"},
                    "bank_account": {"type": "string"},
                    "ifsc_code": {"type": "string"},
                    "avatar_id": {"type": "string", "format": "uuid"}
                }
            },
            response_schema={
                "201": {
                    "message": "Registration successful",
                    "data": {
                        "user": {
                            "id": "uuid",
                            "email": "string",
                            "first_name": "string",
                            "last_name": "string",
                            "role": "string",
                            "is_verified": "boolean"
                        }
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Validation error or email already exists"},
                {"code": 422, "description": "Invalid input data format"}
            ],
            example_request={
                "email": "farmer@agritech.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Farmer",
                "role": "farmer",
                "terms_agreement": True,
                "upi_id": "john@paytm",
                "bank_account": "1234567890123456",
                "ifsc_code": "HDFC0001234"
            },
            example_response={
                "message": "Registration successful",
                "data": {
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "farmer@agritech.com",
                        "first_name": "John",
                        "last_name": "Farmer",
                        "role": "farmer",
                        "is_verified": False
                    }
                }
            }
        ))
        
        # User Login
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/auth/login",
            summary="User Login",
            description="Authenticate user and receive access tokens",
            tags=["Authentication"],
            auth_required=False,
            required_roles=[],
            request_schema={
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string"}
                }
            },
            response_schema={
                "200": {
                    "message": "Login successful",
                    "data": {
                        "access_token": "string",
                        "refresh_token": "string",
                        "token_type": "bearer",
                        "user": {
                            "id": "uuid",
                            "email": "string",
                            "role": "string",
                            "is_verified": "boolean"
                        }
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Invalid credentials"},
                {"code": 429, "description": "Too many login attempts"}
            ],
            example_request={
                "email": "farmer@agritech.com",
                "password": "SecurePass123!"
            },
            example_response={
                "message": "Login successful",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "farmer@agritech.com",
                        "role": "farmer",
                        "is_verified": True
                    }
                }
            }
        ))
        
        # Password Reset Request
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/auth/reset-password",
            summary="Password Reset Request",
            description="Request password reset via email",
            tags=["Authentication"],
            auth_required=False,
            required_roles=[],
            request_schema={
                "type": "object",
                "required": ["email"],
                "properties": {
                    "email": {"type": "string", "format": "email"}
                }
            },
            response_schema={
                "200": {
                    "message": "Password reset email sent",
                    "data": {"email_sent": True}
                }
            },
            error_codes=[
                {"code": 404, "description": "Email not found"}
            ],
            example_request={"email": "farmer@agritech.com"},
            example_response={
                "message": "Password reset email sent",
                "data": {"email_sent": True}
            }
        ))
    
    def add_commodity_endpoints(self):
        """Commodity management endpoints"""
        
        # Create Commodity
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/commodities/",
            summary="Create Commodity Listing",
            description="Create a new commodity listing for auction",
            tags=["Commodities"],
            auth_required=True,
            required_roles=["farmer"],
            request_schema={
                "type": "object",
                "required": ["commodity_name", "quantity_kg", "harvest_date", "min_price"],
                "properties": {
                    "commodity_name": {"type": "string", "maxLength": 100},
                    "description": {"type": "string", "maxLength": 500},
                    "quantity_kg": {"type": "number", "minimum": 0.1},
                    "harvest_date": {"type": "string", "format": "date"},
                    "min_price": {"type": "number", "minimum": 0.01},
                    "closing_date": {"type": "string", "format": "date-time"},
                    "category_id": {"type": "string", "format": "uuid"},
                    "image_id": {"type": "string", "format": "uuid"}
                }
            },
            response_schema={
                "201": {
                    "message": "Commodity created successfully",
                    "data": {
                        "id": "uuid",
                        "commodity_name": "string",
                        "description": "string",
                        "quantity_kg": "number",
                        "min_price": "number",
                        "current_price": "number",
                        "status": "string",
                        "seller_id": "uuid",
                        "created_at": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Validation error"},
                {"code": 401, "description": "Authentication required"},
                {"code": 403, "description": "Farmer role required"}
            ],
            example_request={
                "commodity_name": "Premium Basmati Rice",
                "description": "High-quality aged basmati rice from Punjab",
                "quantity_kg": 1000.0,
                "harvest_date": "2025-01-15",
                "min_price": 45.50,
                "closing_date": "2025-08-01T12:00:00Z"
            },
            example_response={
                "message": "Commodity created successfully",
                "data": {
                    "id": "987fcdeb-51a2-43d7-b456-426614174000",
                    "commodity_name": "Premium Basmati Rice",
                    "description": "High-quality aged basmati rice from Punjab",
                    "quantity_kg": 1000.0,
                    "min_price": 45.50,
                    "current_price": 45.50,
                    "status": "active",
                    "seller_id": "123e4567-e89b-12d3-a456-426614174000",
                    "created_at": "2025-07-20T10:30:00Z"
                }
            }
        ))
        
        # Get All Commodities
        self.endpoints.append(APIEndpoint(
            method="GET",
            path="/api/v1/commodities/",
            summary="Get All Commodities",
            description="Retrieve all active commodity listings with pagination",
            tags=["Commodities"],
            auth_required=False,
            required_roles=[],
            request_schema=None,
            response_schema={
                "200": {
                    "message": "Commodities retrieved successfully",
                    "data": [
                        {
                            "id": "uuid",
                            "commodity_name": "string",
                            "description": "string",
                            "quantity_kg": "number",
                            "min_price": "number",
                            "current_price": "number",
                            "status": "string",
                            "seller": {
                                "id": "uuid",
                                "first_name": "string",
                                "last_name": "string"
                            },
                            "bids_count": "number",
                            "closing_date": "datetime"
                        }
                    ],
                    "pagination": {
                        "page": "number",
                        "per_page": "number",
                        "total": "number",
                        "pages": "number"
                    }
                }
            },
            error_codes=[],
            example_request=None,
            example_response={
                "message": "Commodities retrieved successfully",
                "data": [
                    {
                        "id": "987fcdeb-51a2-43d7-b456-426614174000",
                        "commodity_name": "Premium Basmati Rice",
                        "description": "High-quality aged basmati rice",
                        "quantity_kg": 1000.0,
                        "min_price": 45.50,
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
        ))
    
    def add_bidding_endpoints(self):
        """Bidding system endpoints"""
        
        # Place Bid
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/bidding/place-bid",
            summary="Place Bid",
            description="Place a bid on a commodity listing",
            tags=["Bidding"],
            auth_required=True,
            required_roles=["trader"],
            request_schema={
                "type": "object",
                "required": ["commodity_listing_id", "amount"],
                "properties": {
                    "commodity_listing_id": {"type": "string", "format": "uuid"},
                    "amount": {"type": "number", "minimum": 0.01}
                }
            },
            response_schema={
                "201": {
                    "message": "Bid placed successfully",
                    "data": {
                        "id": "uuid",
                        "commodity_listing_id": "uuid",
                        "bidder_id": "uuid",
                        "amount": "number",
                        "status": "string",
                        "created_at": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Bid amount too low or invalid"},
                {"code": 401, "description": "Authentication required"},
                {"code": 403, "description": "Trader role required or KYC not verified"},
                {"code": 404, "description": "Commodity not found"}
            ],
            example_request={
                "commodity_listing_id": "987fcdeb-51a2-43d7-b456-426614174000",
                "amount": 50.00
            },
            example_response={
                "message": "Bid placed successfully",
                "data": {
                    "id": "456e7890-f12c-34e5-d678-901234567890",
                    "commodity_listing_id": "987fcdeb-51a2-43d7-b456-426614174000",
                    "bidder_id": "789abc12-3456-78de-f012-345678901234",
                    "amount": 50.00,
                    "status": "active",
                    "created_at": "2025-07-20T14:30:00Z"
                }
            }
        ))
    
    def add_price_tracking_endpoints(self):
        """Price tracking and alerts endpoints"""
        
        # Create Price Alert
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/price-tracking/alerts",
            summary="Create Price Alert",
            description="Set up price alert notification for a commodity",
            tags=["Price Tracking"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema={
                "type": "object",
                "required": ["commodity_id", "threshold_price", "direction"],
                "properties": {
                    "commodity_id": {"type": "string", "format": "uuid"},
                    "threshold_price": {"type": "number", "minimum": 0.01},
                    "direction": {"type": "string", "enum": ["ABOVE", "BELOW"]},
                    "notify_email": {"type": "boolean", "default": True},
                    "notify_sms": {"type": "boolean", "default": False},
                    "notify_onsite": {"type": "boolean", "default": True}
                }
            },
            response_schema={
                "201": {
                    "message": "Price alert created successfully",
                    "data": {
                        "id": "uuid",
                        "commodity_id": "uuid",
                        "user_id": "uuid",
                        "threshold_price": "number",
                        "direction": "string",
                        "active": "boolean",
                        "created_at": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Invalid alert parameters"},
                {"code": 401, "description": "Authentication required"},
                {"code": 404, "description": "Commodity not found"}
            ],
            example_request={
                "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
                "threshold_price": 45.00,
                "direction": "BELOW",
                "notify_email": True,
                "notify_sms": True
            },
            example_response={
                "message": "Price alert created successfully",
                "data": {
                    "id": "alert123-4567-89ab-cdef-012345678901",
                    "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
                    "user_id": "789abc12-3456-78de-f012-345678901234",
                    "threshold_price": 45.00,
                    "direction": "BELOW",
                    "active": True,
                    "created_at": "2025-07-20T15:00:00Z"
                }
            }
        ))
    
    def add_ml_recommendation_endpoints(self):
        """ML recommendations endpoints"""
        
        # Get Commodity Recommendation
        self.endpoints.append(APIEndpoint(
            method="GET",
            path="/api/v6/recommendations/suggestions/{commodity_slug}",
            summary="Get ML Trading Recommendation",
            description="Get AI-powered trading recommendation for a specific commodity",
            tags=["ML Recommendations"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema=None,
            response_schema={
                "200": {
                    "message": "Recommendation generated successfully",
                    "data": {
                        "commodity_slug": "string",
                        "suggestion": "string (BUY/SELL/HOLD)",
                        "confidence": "number (0-1)",
                        "current_price": "number",
                        "predicted_price": "number",
                        "avg_price_30d": "number",
                        "avg_price_7d": "number",
                        "volatility": "number",
                        "weekly_trend": "number",
                        "monthly_trend": "number",
                        "reasoning": "string",
                        "risk_level": "string",
                        "timestamp": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Insufficient data for prediction"},
                {"code": 401, "description": "Authentication required"},
                {"code": 404, "description": "Commodity not found"}
            ],
            example_request=None,
            example_response={
                "message": "Recommendation generated successfully",
                "data": {
                    "commodity_slug": "premium-basmati-rice",
                    "suggestion": "BUY",
                    "confidence": 0.85,
                    "current_price": 48.75,
                    "predicted_price": 52.30,
                    "avg_price_30d": 46.20,
                    "avg_price_7d": 48.10,
                    "volatility": 0.12,
                    "weekly_trend": 0.025,
                    "monthly_trend": 0.055,
                    "reasoning": "Price trending upward with strong demand indicators",
                    "risk_level": "medium",
                    "timestamp": "2025-07-20T16:00:00Z"
                }
            }
        ))
        
        # Get Market Overview
        self.endpoints.append(APIEndpoint(
            method="GET",
            path="/api/v6/recommendations/market-overview",
            summary="Get Market Overview",
            description="Get AI-powered market sentiment and trading opportunities",
            tags=["ML Recommendations"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema=None,
            response_schema={
                "200": {
                    "message": "Market overview generated successfully",
                    "data": {
                        "market_sentiment": {
                            "buy_percentage": "number",
                            "sell_percentage": "number",
                            "hold_percentage": "number"
                        },
                        "top_buy_opportunities": [
                            {
                                "commodity_slug": "string",
                                "suggestion": "BUY",
                                "confidence": "number",
                                "current_price": "number",
                                "reasoning": "string"
                            }
                        ],
                        "top_sell_opportunities": [
                            {
                                "commodity_slug": "string",
                                "suggestion": "SELL",
                                "confidence": "number",
                                "current_price": "number",
                                "reasoning": "string"
                            }
                        ],
                        "total_analyzed": "number",
                        "timestamp": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 401, "description": "Authentication required"}
            ],
            example_request=None,
            example_response={
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
                            "current_price": 28.50,
                            "reasoning": "Strong seasonal demand expected"
                        }
                    ],
                    "total_analyzed": 45,
                    "timestamp": "2025-07-20T16:00:00Z"
                }
            }
        ))
    
    def add_admin_endpoints(self):
        """Admin-only endpoints"""
        
        # KYC Verification
        self.endpoints.append(APIEndpoint(
            method="PATCH",
            path="/api/v1/auth/verify-kyc/{user_id}",
            summary="Verify User KYC",
            description="Admin endpoint to verify user's KYC status",
            tags=["Admin"],
            auth_required=True,
            required_roles=["admin"],
            request_schema={
                "type": "object",
                "required": ["is_verified"],
                "properties": {
                    "is_verified": {"type": "boolean"},
                    "verification_notes": {"type": "string"}
                }
            },
            response_schema={
                "200": {
                    "message": "KYC verification updated successfully",
                    "data": {
                        "user_id": "uuid",
                        "is_verified": "boolean",
                        "verified_at": "datetime",
                        "verified_by": "uuid"
                    }
                }
            },
            error_codes=[
                {"code": 401, "description": "Authentication required"},
                {"code": 403, "description": "Admin role required"},
                {"code": 404, "description": "User not found"}
            ],
            example_request={
                "is_verified": True,
                "verification_notes": "All documents verified successfully"
            },
            example_response={
                "message": "KYC verification updated successfully",
                "data": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "is_verified": True,
                    "verified_at": "2025-07-20T16:30:00Z",
                    "verified_by": "admin456-7890-abcd-ef12-345678901234"
                }
            }
        ))
    
    def add_general_endpoints(self):
        """General utility endpoints"""
        
        # Health Check
        self.endpoints.append(APIEndpoint(
            method="GET",
            path="/api/v1/general/health",
            summary="Health Check",
            description="Check API health status",
            tags=["General"],
            auth_required=False,
            required_roles=[],
            request_schema=None,
            response_schema={
                "200": {
                    "message": "AgriTech API is healthy",
                    "data": {
                        "status": "healthy",
                        "timestamp": "datetime",
                        "version": "string",
                        "services": {
                            "database": "string",
                            "redis": "string",
                            "ml_engine": "string"
                        }
                    }
                }
            },
            error_codes=[],
            example_request=None,
            example_response={
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
        ))
        
        # Image Upload
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/general/upload-image",
            summary="Upload Image",
            description="Upload image file for profile or product listing",
            tags=["General"],
            auth_required=False,
            required_roles=[],
            request_schema={
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Image file (JPEG, PNG, WEBP, max 5MB)"
                    }
                }
            },
            response_schema={
                "200": {
                    "message": "Image uploaded successfully",
                    "data": {
                        "file_id": "uuid",
                        "filename": "string",
                        "content_type": "string",
                        "size": "number"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Invalid file type or size"},
                {"code": 413, "description": "File too large"}
            ],
            example_request=None,
            example_response={
                "message": "Image uploaded successfully",
                "data": {
                    "file_id": "img12345-6789-abcd-ef01-234567890123",
                    "filename": "product_image.jpg",
                    "content_type": "image/jpeg",
                    "size": 245760
                }
            }
        ))
    
    def add_auctioneer_endpoints(self):
        """Auctioneer (general listing) endpoints"""
        
        # Create General Listing
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/v1/auctioneer/",
            summary="Create General Listing",
            description="Create a general auction listing (non-commodity)",
            tags=["Auctioneer"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema={
                "type": "object",
                "required": ["name", "desc", "price", "closing_date", "file_type", "image_id"],
                "properties": {
                    "name": {"type": "string", "maxLength": 100},
                    "desc": {"type": "string", "maxLength": 500},
                    "category": {"type": "string"},
                    "price": {"type": "number", "minimum": 0.01},
                    "closing_date": {"type": "string", "format": "date-time"},
                    "file_type": {"type": "string"},
                    "image_id": {"type": "string", "format": "uuid"}
                }
            },
            response_schema={
                "201": {
                    "message": "Listing created successfully",
                    "data": {
                        "id": "uuid",
                        "name": "string",
                        "desc": "string",
                        "price": "number",
                        "status": "string",
                        "seller_id": "uuid",
                        "created_at": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Validation error"},
                {"code": 401, "description": "Authentication required"}
            ],
            example_request={
                "name": "Agricultural Equipment",
                "desc": "High-quality tractor for sale",
                "category": "Equipment",
                "price": 250000.00,
                "closing_date": "2025-08-15T18:00:00Z",
                "file_type": "equipment",
                "image_id": "img12345-6789-abcd-ef01-234567890123"
            },
            example_response={
                "message": "Listing created successfully",
                "data": {
                    "id": "listing1-2345-6789-abcd-ef0123456789",
                    "name": "Agricultural Equipment",
                    "desc": "High-quality tractor for sale",
                    "price": 250000.00,
                    "status": "active",
                    "seller_id": "123e4567-e89b-12d3-a456-426614174000",
                    "created_at": "2025-07-20T18:00:00Z"
                }
            }
        ))
    
    def add_websocket_endpoints(self):
        """WebSocket endpoints for real-time features"""
        
        # Real-time Bidding WebSocket
        self.endpoints.append(APIEndpoint(
            method="WebSocket",
            path="/ws/bidding/{commodity_id}",
            summary="Real-time Bidding Updates",
            description="WebSocket connection for real-time bidding updates",
            tags=["WebSocket"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["subscribe", "unsubscribe", "bid"]},
                    "data": {"type": "object"}
                }
            },
            response_schema={
                "message": {
                    "type": "string",
                    "event": "string",
                    "data": {
                        "commodity_id": "uuid",
                        "new_bid": {
                            "id": "uuid",
                            "amount": "number",
                            "bidder": "string",
                            "timestamp": "datetime"
                        }
                    }
                }
            },
            error_codes=[
                {"code": 401, "description": "Authentication required"},
                {"code": 404, "description": "Commodity not found"}
            ],
            example_request={
                "action": "subscribe",
                "data": {"commodity_id": "987fcdeb-51a2-43d7-b456-426614174000"}
            },
            example_response={
                "type": "bid_update",
                "event": "new_bid",
                "data": {
                    "commodity_id": "987fcdeb-51a2-43d7-b456-426614174000",
                    "new_bid": {
                        "id": "bid12345-6789-abcd-ef01-234567890123",
                        "amount": 52.00,
                        "bidder": "Trader John",
                        "timestamp": "2025-07-20T18:30:00Z"
                    }
                }
            }
        ))
    
    def add_mobile_endpoints(self):
        """Mobile and notification endpoints"""
        
        # Register Device
        self.endpoints.append(APIEndpoint(
            method="POST",
            path="/mobile/register-device",
            summary="Register Mobile Device",
            description="Register mobile device for push notifications",
            tags=["Mobile"],
            auth_required=True,
            required_roles=["farmer", "trader"],
            request_schema={
                "type": "object",
                "required": ["device_token", "device_type", "app_version"],
                "properties": {
                    "device_token": {"type": "string"},
                    "device_type": {"type": "string", "enum": ["ios", "android"]},
                    "app_version": {"type": "string"},
                    "device_name": {"type": "string"}
                }
            },
            response_schema={
                "201": {
                    "message": "Device registered successfully",
                    "data": {
                        "device_id": "uuid",
                        "device_token": "string",
                        "device_type": "string",
                        "registered_at": "datetime"
                    }
                }
            },
            error_codes=[
                {"code": 400, "description": "Invalid device data"},
                {"code": 401, "description": "Authentication required"}
            ],
            example_request={
                "device_token": "dGVzdF9kZXZpY2VfdG9rZW4=",
                "device_type": "android",
                "app_version": "1.0.0",
                "device_name": "Samsung Galaxy S21"
            },
            example_response={
                "message": "Device registered successfully",
                "data": {
                    "device_id": "device12-3456-7890-abcd-ef0123456789",
                    "device_token": "dGVzdF9kZXZpY2VfdG9rZW4=",
                    "device_type": "android",
                    "registered_at": "2025-07-20T19:00:00Z"
                }
            }
        ))
    
    def generate_markdown_documentation(self) -> str:
        """Generate comprehensive markdown documentation"""
        
        doc = """# AgriTech Platform API Documentation

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

"""
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for endpoint in self.endpoints:
            for tag in endpoint.tags:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        # Generate documentation for each tag group
        for tag, endpoints in endpoints_by_tag.items():
            doc += f"## {tag}\n\n"
            
            for endpoint in endpoints:
                doc += f"### {endpoint.method} {endpoint.path}\n\n"
                doc += f"**{endpoint.summary}**\n\n"
                doc += f"{endpoint.description}\n\n"
                
                # Authentication info
                if endpoint.auth_required:
                    roles_text = ", ".join(endpoint.required_roles) if endpoint.required_roles else "any authenticated user"
                    doc += f"**Authentication**: Required ({roles_text})\n\n"
                else:
                    doc += f"**Authentication**: Not required\n\n"
                
                # Request schema
                if endpoint.request_schema:
                    doc += "**Request Body**:\n```json\n"
                    doc += json.dumps(endpoint.example_request, indent=2)
                    doc += "\n```\n\n"
                
                # Response schema
                doc += "**Response**:\n```json\n"
                doc += json.dumps(endpoint.example_response, indent=2)
                doc += "\n```\n\n"
                
                # Error codes
                if endpoint.error_codes:
                    doc += "**Error Codes**:\n"
                    for error in endpoint.error_codes:
                        doc += f"- `{error['code']}`: {error['description']}\n"
                    doc += "\n"
                
                doc += "---\n\n"
        
        # Add additional sections
        doc += self._add_usage_examples()
        doc += self._add_security_notes()
        doc += self._add_changelog()
        
        return doc
    
    def _add_usage_examples(self) -> str:
        """Add usage examples section"""
        return """## Usage Examples

### Complete User Journey

#### 1. User Registration
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
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
curl -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "farmer@example.com",
    "password": "SecurePass123!"
  }'
```

#### 3. Create Commodity Listing
```bash
curl -X POST http://localhost:8000/api/v1/commodities/ \\
  -H "Authorization: Bearer <your_token>" \\
  -H "Content-Type: application/json" \\
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
curl -X POST http://localhost:8000/api/v1/bidding/place-bid \\
  -H "Authorization: Bearer <trader_token>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "commodity_listing_id": "commodity_id_here",
    "amount": 30.00
  }'
```

#### 5. Get ML Recommendation
```bash
curl -X GET http://localhost:8000/api/v6/recommendations/suggestions/wheat-premium \\
  -H "Authorization: Bearer <your_token>"
```

---

"""
    
    def _add_security_notes(self) -> str:
        """Add security notes section"""
        return """## Security

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

"""
    
    def _add_changelog(self) -> str:
        """Add changelog section"""
        return """## Changelog

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
*API Version: 6.0.0*
*Documentation generated automatically*
"""


def generate_complete_api_documentation():
    """Generate and save complete API documentation"""
    
    print("📚 Generating Complete API Documentation...")
    print("=" * 60)
    
    # Generate documentation
    doc_generator = APIDocumentationGenerator()
    markdown_doc = doc_generator.generate_markdown_documentation()
    
    # Save to file
    with open("API_DOCUMENTATION.md", "w", encoding="utf-8") as f:
        f.write(markdown_doc)
    
    # Generate JSON schema for programmatic access
    json_schema = {
        "api_version": "6.0.0",
        "generated_at": datetime.now().isoformat(),
        "base_url": "http://localhost:8000",
        "endpoints": []
    }
    
    for endpoint in doc_generator.endpoints:
        json_schema["endpoints"].append({
            "method": endpoint.method,
            "path": endpoint.path,
            "summary": endpoint.summary,
            "description": endpoint.description,
            "tags": endpoint.tags,
            "auth_required": endpoint.auth_required,
            "required_roles": endpoint.required_roles,
            "request_schema": endpoint.request_schema,
            "response_schema": endpoint.response_schema,
            "error_codes": endpoint.error_codes,
            "example_request": endpoint.example_request,
            "example_response": endpoint.example_response
        })
    
    with open("API_SCHEMA.json", "w", encoding="utf-8") as f:
        json.dump(json_schema, f, indent=2)
    
    print(f"✅ Documentation generated:")
    print(f"   📄 API_DOCUMENTATION.md ({len(markdown_doc):,} characters)")
    print(f"   📋 API_SCHEMA.json ({len(doc_generator.endpoints)} endpoints)")
    print(f"   🏷️  API Tags: {len(set(tag for endpoint in doc_generator.endpoints for tag in endpoint.tags))}")
    
    # Generate summary statistics
    auth_required = sum(1 for e in doc_generator.endpoints if e.auth_required)
    methods = {}
    for endpoint in doc_generator.endpoints:
        methods[endpoint.method] = methods.get(endpoint.method, 0) + 1
    
    print(f"\n📊 API Statistics:")
    print(f"   Total Endpoints: {len(doc_generator.endpoints)}")
    print(f"   Authenticated: {auth_required}")
    print(f"   Public: {len(doc_generator.endpoints) - auth_required}")
    
    for method, count in sorted(methods.items()):
        print(f"   {method}: {count}")
    
    print(f"\n🎯 Phase 7: Security and Testing - Documentation Complete!")
    
    return {
        "total_endpoints": len(doc_generator.endpoints),
        "authenticated_endpoints": auth_required,
        "public_endpoints": len(doc_generator.endpoints) - auth_required,
        "methods": methods,
        "documentation_files": ["API_DOCUMENTATION.md", "API_SCHEMA.json"]
    }


if __name__ == "__main__":
    generate_complete_api_documentation()
