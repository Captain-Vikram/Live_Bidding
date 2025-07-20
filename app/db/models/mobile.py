"""
Mobile and Device Management Models
===================================

SQLAlchemy models for mobile device registration and management
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from enum import Enum
import uuid
from datetime import datetime

from app.db.models.base import BaseModel


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


class DeviceRegistration(BaseModel):
    """Mobile device registration for push notifications"""
    
    __tablename__ = "device_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_token = Column(String(255), nullable=False, unique=True)
    device_type = Column(SQLEnum(DeviceType), nullable=False)
    device_info = Column(JSONB, nullable=True)  # Store device details
    app_version = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="devices")
    
    def __repr__(self):
        return f"<DeviceRegistration {self.device_type} for user {self.user_id}>"


class NotificationPreference(BaseModel):
    """User notification preferences"""
    
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification channels
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Notification types
    trade_updates = Column(Boolean, default=True)
    market_reminders = Column(Boolean, default=True)
    price_alerts = Column(Boolean, default=True)
    listing_updates = Column(Boolean, default=True)
    payment_notifications = Column(Boolean, default=True)
    marketing_notifications = Column(Boolean, default=False)
    
    # Timing preferences
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "07:00"
    timezone = Column(String(50), default="UTC")
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreference for user {self.user_id}>"


class NotificationLog(BaseModel):
    """Log of sent notifications"""
    
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String(100), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB, nullable=True)  # Additional data
    
    # Delivery status
    status = Column(String(50), default="pending")  # pending, sent, delivered, failed
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Tracking
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notification_logs")
    
    def __repr__(self):
        return f"<NotificationLog {self.notification_type} to {self.user_id}>"


class UserActivity(BaseModel):
    """Track user activity for analytics and recommendations"""
    
    __tablename__ = "user_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Activity details
    activity_type = Column(String(100), nullable=False)  # view, search, bid, etc.
    resource_type = Column(String(50), nullable=True)    # listing, auction, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Context data
    data = Column(JSONB, nullable=True)  # Activity-specific data
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    location_data = Column(JSONB, nullable=True)  # Geo data if available
    
    # Timing
    duration_seconds = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity {self.activity_type} by {self.user_id}>"


class UserLocation(BaseModel):
    """Store user location data for location-based features"""
    
    __tablename__ = "user_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Location coordinates
    latitude = Column(String(50), nullable=False)
    longitude = Column(String(50), nullable=False)
    accuracy = Column(Integer, nullable=True)  # Accuracy in meters
    
    # Address details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Location context
    is_primary = Column(Boolean, default=False)
    location_type = Column(String(50), nullable=True)  # home, farm, market, etc.
    
    # Relationships
    user = relationship("User", back_populates="locations")
    
    def __repr__(self):
        return f"<UserLocation {self.city}, {self.state} for {self.user_id}>"
