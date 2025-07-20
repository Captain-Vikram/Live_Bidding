"""
Mobile and Notification API Schemas
===================================

Pydantic models for mobile device management and notification endpoints
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import UUID

from app.api.schemas.base import BaseAPISchema


class DeviceType(str, Enum):
    """Device type enumeration"""
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    DESKTOP = "desktop"


class NotificationChannel(str, Enum):
    """Notification channel enumeration"""
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


# ===== DEVICE REGISTRATION SCHEMAS =====

class DeviceRegistrationCreate(BaseAPISchema):
    """Schema for device registration"""
    device_token: str = Field(..., description="Device token for push notifications")
    device_type: DeviceType = Field(..., description="Type of device")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Additional device information")
    app_version: Optional[str] = Field(None, description="App version")
    os_version: Optional[str] = Field(None, description="OS version")


class DeviceRegistrationResponse(BaseAPISchema):
    """Schema for device registration response"""
    id: UUID
    device_token: str
    device_type: DeviceType
    device_info: Optional[Dict[str, Any]]
    app_version: Optional[str]
    os_version: Optional[str]
    is_active: bool
    last_active: datetime
    created_at: datetime


class DeviceListResponse(BaseAPISchema):
    """Schema for device list response"""
    devices: List[DeviceRegistrationResponse]
    total: int


# ===== NOTIFICATION PREFERENCE SCHEMAS =====

class NotificationPreferenceUpdate(BaseAPISchema):
    """Schema for updating notification preferences"""
    # Channel preferences
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    
    # Notification type preferences
    trade_updates: Optional[bool] = None
    market_reminders: Optional[bool] = None
    price_alerts: Optional[bool] = None
    listing_updates: Optional[bool] = None
    payment_notifications: Optional[bool] = None
    marketing_notifications: Optional[bool] = None
    
    # Timing preferences
    quiet_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None


class NotificationPreferenceResponse(BaseAPISchema):
    """Schema for notification preference response"""
    id: UUID
    user_id: UUID
    
    # Channel preferences
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    
    # Notification type preferences
    trade_updates: bool
    market_reminders: bool
    price_alerts: bool
    listing_updates: bool
    payment_notifications: bool
    marketing_notifications: bool
    
    # Timing preferences
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    timezone: str
    
    created_at: datetime
    updated_at: datetime


# ===== NOTIFICATION LOG SCHEMAS =====

class NotificationLogResponse(BaseAPISchema):
    """Schema for notification log response"""
    id: UUID
    notification_type: str
    channel: NotificationChannel
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    status: str
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    clicked: bool
    clicked_at: Optional[datetime]
    created_at: datetime


class NotificationHistoryResponse(BaseAPISchema):
    """Schema for notification history response"""
    notifications: List[NotificationLogResponse]
    total: int
    has_more: bool


class NotificationAnalyticsResponse(BaseAPISchema):
    """Schema for notification analytics"""
    total_notifications: int
    channel_stats: List[Dict[str, Any]]
    overall_click_rate: float


# ===== PUSH NOTIFICATION SCHEMAS =====

class PushNotificationSend(BaseAPISchema):
    """Schema for sending push notifications"""
    user_ids: Optional[List[UUID]] = Field(None, description="Specific users to notify")
    device_types: Optional[List[DeviceType]] = Field(None, description="Device types to target")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    notification_type: str = Field("general", description="Type of notification")
    
    @validator('user_ids', 'device_types')
    def validate_targeting(cls, v, values):
        if not v and not values.get('device_types'):
            raise ValueError("Must specify either user_ids or device_types")
        return v


class PushNotificationResponse(BaseAPISchema):
    """Schema for push notification response"""
    message: str
    sent_count: int
    failed_count: int
    notification_ids: List[UUID]


# ===== USER ACTIVITY SCHEMAS =====

class UserActivityCreate(BaseAPISchema):
    """Schema for tracking user activity"""
    activity_type: str = Field(..., description="Type of activity")
    resource_type: Optional[str] = Field(None, description="Type of resource")
    resource_id: Optional[UUID] = Field(None, description="ID of resource")
    data: Optional[Dict[str, Any]] = Field(None, description="Activity data")
    duration_seconds: Optional[int] = Field(None, description="Activity duration")


class UserActivityResponse(BaseAPISchema):
    """Schema for user activity response"""
    id: UUID
    activity_type: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    data: Optional[Dict[str, Any]]
    duration_seconds: Optional[int]
    created_at: datetime


class UserActivitySummaryResponse(BaseAPISchema):
    """Schema for user activity summary"""
    activity_counts: Dict[str, int]
    top_viewed_resources: List[Dict[str, Any]]
    period_days: int


# ===== USER LOCATION SCHEMAS =====

class UserLocationCreate(BaseAPISchema):
    """Schema for creating user location"""
    latitude: str = Field(..., description="Latitude coordinate")
    longitude: str = Field(..., description="Longitude coordinate")
    accuracy: Optional[int] = Field(None, description="Location accuracy in meters")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")
    location_type: Optional[str] = Field("current", description="Type of location")
    is_primary: bool = Field(False, description="Is this the primary location")


class UserLocationResponse(BaseAPISchema):
    """Schema for user location response"""
    id: UUID
    latitude: str
    longitude: str
    accuracy: Optional[int]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    location_type: Optional[str]
    is_primary: bool
    created_at: datetime


class LocationListResponse(BaseAPISchema):
    """Schema for location list response"""
    locations: List[UserLocationResponse]
    total: int


# ===== PWA AND MOBILE APP SCHEMAS =====

class PWAManifestResponse(BaseAPISchema):
    """Schema for PWA manifest"""
    name: str
    short_name: str
    description: str
    start_url: str
    display: str
    background_color: str
    theme_color: str
    orientation: str
    icons: List[Dict[str, Any]]


class AppConfigResponse(BaseAPISchema):
    """Schema for mobile app configuration"""
    api_base_url: str
    websocket_url: str
    features: Dict[str, bool]
    version: str
    minimum_app_version: str
    update_required: bool
    maintenance_mode: bool


class QRCodeGenerateRequest(BaseAPISchema):
    """Schema for QR code generation"""
    data: str = Field(..., description="Data to encode in QR code")
    size: int = Field(200, description="QR code size in pixels", ge=100, le=1000)
    error_correction: str = Field("M", description="Error correction level")


class QRCodeResponse(BaseAPISchema):
    """Schema for QR code response"""
    qr_code_url: str
    data: str
    expires_at: Optional[datetime]


# ===== MOBILE SEARCH AND RECOMMENDATIONS =====

class MobileSearchRequest(BaseAPISchema):
    """Schema for mobile-optimized search"""
    query: str = Field(..., description="Search query")
    category_id: Optional[UUID] = None
    location_radius_km: Optional[int] = Field(None, ge=1, le=100)
    price_min: Optional[float] = Field(None, ge=0)
    price_max: Optional[float] = None
    sort_by: str = Field("relevance", description="Sort criteria")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class RecommendationRequest(BaseAPISchema):
    """Schema for getting recommendations"""
    recommendation_type: str = Field("listings", description="Type of recommendations")
    limit: int = Field(10, ge=1, le=50)
    context: Optional[Dict[str, Any]] = Field(None, description="Recommendation context")


class RecommendationResponse(BaseAPISchema):
    """Schema for recommendation response"""
    recommendations: List[Dict[str, Any]]
    recommendation_type: str
    algorithm: str
    confidence_score: Optional[float]


# ===== MOBILE PERFORMANCE MONITORING =====

class PerformanceMetrics(BaseAPISchema):
    """Schema for mobile performance metrics"""
    app_version: str
    device_type: DeviceType
    os_version: str
    network_type: str
    
    # Performance metrics
    app_launch_time: Optional[float] = None
    api_response_times: Optional[Dict[str, float]] = None
    crash_count: int = 0
    memory_usage_mb: Optional[float] = None
    battery_level: Optional[int] = None
    
    # User experience metrics
    session_duration: Optional[int] = None
    screen_views: Optional[List[str]] = None
    user_interactions: Optional[Dict[str, int]] = None


class PerformanceMetricsResponse(BaseAPISchema):
    """Schema for performance metrics response"""
    message: str
    metrics_recorded: bool
    recommendations: Optional[List[str]] = None
