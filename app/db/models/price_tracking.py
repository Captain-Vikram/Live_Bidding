"""
Phase 5: Price History and Alerts Implementation
===============================================

Enhanced price tracking and alert subscription functionality with on-site notifications
"""

from sqlalchemy import Column, String, Date, Float, ForeignKey, Enum, Boolean, DateTime, Text, Index, Integer
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as GUUID
import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.listings import CommodityListing
    from app.db.models.accounts import User

# Additional enums for enhanced functionality
class PriceSource(enum.Enum):
    """Price data source types"""
    INTERNAL = "INTERNAL"
    MANUAL = "MANUAL"
    AGMARKNET = "AGMARKNET"
    ENAM = "ENAM"
    AUCTION_BASED = "AUCTION_BASED"

class NotificationChannel(enum.Enum):
    """Notification delivery channels"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    ONSITE = "ONSITE"  # New: On-site notifications

class NotificationStatus(enum.Enum):
    """Notification delivery status"""
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    READ = "READ"

class AlertDirection(enum.Enum):
    BUY = "buy"
    SELL = "sell"

class PriceHistory(BaseModel):
    """Historical price data for commodities"""
    __tablename__ = "price_history"

    commodity_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("commodity_listings.id", ondelete="CASCADE")
    )
    commodity: Mapped["CommodityListing"] = relationship("CommodityListing", lazy="joined")
    
    date: Mapped[datetime] = Column(Date, nullable=False)
    avg_price: Mapped[float] = Column(Float, nullable=False)
    high_price: Mapped[float] = Column(Float, nullable=False)
    low_price: Mapped[float] = Column(Float, nullable=False)
    volume_kg: Mapped[float] = Column(Float, default=0.0)
    
    # Market/source information
    market_name: Mapped[str] = Column(String(100), nullable=True)
    source: Mapped[str] = Column(String(50), default="manual")  # manual, agmarknet, enam
    
    def __repr__(self):
        return f"PriceHistory({self.commodity.commodity_name} - {self.date}: ₹{self.avg_price}/kg)"

class AlertSubscription(BaseModel):
    """User alert subscriptions for price thresholds"""
    __tablename__ = "alert_subscriptions"
    
    user_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship("User", lazy="joined")
    
    commodity_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("commodity_listings.id", ondelete="CASCADE")
    )
    commodity: Mapped["CommodityListing"] = relationship("CommodityListing", lazy="joined")
    
    threshold_price: Mapped[float] = Column(Float, nullable=False)
    threshold_pct: Mapped[float] = Column(Float, nullable=True)  # Percentage change threshold
    direction: Mapped[AlertDirection] = Column(Enum(AlertDirection), nullable=False)
    
    is_active: Mapped[bool] = Column(Boolean, default=True)
    last_triggered: Mapped[datetime] = Column(DateTime, nullable=True)
    
    # Notification preferences
    notify_email: Mapped[bool] = Column(Boolean, default=True)
    notify_sms: Mapped[bool] = Column(Boolean, default=False)
    notify_push: Mapped[bool] = Column(Boolean, default=True)
    notify_onsite: Mapped[bool] = Column(Boolean, default=True)  # NEW: On-site notifications
    
    # Enhanced alert control
    max_triggers_per_day: Mapped[int] = Column(Integer, default=3)
    trigger_count_today: Mapped[int] = Column(Integer, default=0)
    
    def __repr__(self):
        return f"Alert({self.user.email} - {self.commodity.commodity_name}: ₹{self.threshold_price} {self.direction.value})"

class PriceAlert(BaseModel):
    """Log of triggered price alerts"""
    __tablename__ = "price_alerts"
    
    subscription_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("alert_subscriptions.id", ondelete="CASCADE")
    )
    subscription: Mapped[AlertSubscription] = relationship("AlertSubscription", lazy="joined")
    
    triggered_price: Mapped[float] = Column(Float, nullable=False)
    threshold_price: Mapped[float] = Column(Float, nullable=False)
    price_change_pct: Mapped[float] = Column(Float, nullable=True)
    
    message: Mapped[str] = Column(String(500), nullable=True)
    
    # Delivery status
    email_sent: Mapped[bool] = Column(Boolean, default=False)
    sms_sent: Mapped[bool] = Column(Boolean, default=False)
    push_sent: Mapped[bool] = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"PriceAlert({self.subscription.commodity.commodity_name}: ₹{self.triggered_price})"

# NEW ENHANCED MODELS FOR PHASE 5

class OnSiteNotification(BaseModel):
    """On-site notifications for active users"""
    __tablename__ = "onsite_notifications"
    
    # User and notification details
    user_id: Mapped[GUUID] = Column(UUID(as_uuid=True), ForeignKey("users.pkid"), nullable=False, index=True)
    title: Mapped[str] = Column(String(200), nullable=False)
    message: Mapped[str] = Column(Text, nullable=False)
    notification_type: Mapped[str] = Column(String(50), nullable=False, index=True)  # PRICE_ALERT, BID_UPDATE, etc.
    
    # Status and metadata
    is_read: Mapped[bool] = Column(Boolean(), default=False, index=True)
    is_urgent: Mapped[bool] = Column(Boolean(), default=False)
    read_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # Related data (JSON for flexibility)
    extra_data: Mapped[Optional[str]] = Column(Text, nullable=True)  # JSON string
    action_url: Mapped[Optional[str]] = Column(String(500), nullable=True)  # Link for "View Details"
    
    # Relationships
    user = relationship("User", back_populates="onsite_notifications")
    
    # Add index for efficient queries
    __table_args__ = (
        Index('idx_user_unread', 'user_id', 'is_read'),
        Index('idx_user_type', 'user_id', 'notification_type'),
    )
    
    def __repr__(self):
        return f"<OnSiteNotification(user_id='{self.user_id}', type='{self.notification_type}', read='{self.is_read}')>"

class PriceNotificationLog(BaseModel):
    """Enhanced log of all notification deliveries"""
    __tablename__ = "price_notification_logs"
    
    # User and notification details
    user_id: Mapped[GUUID] = Column(UUID(as_uuid=True), ForeignKey("users.pkid"), nullable=False, index=True)
    alert_subscription_id: Mapped[Optional[GUUID]] = Column(UUID(as_uuid=True), ForeignKey("alert_subscriptions.id"), nullable=True)
    
    # Notification content
    channel: Mapped[str] = Column(String(20), nullable=False)  # EMAIL, SMS, PUSH, ONSITE
    title: Mapped[str] = Column(String(200), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    
    # Delivery tracking
    status: Mapped[str] = Column(String(20), default="PENDING")  # PENDING, SENT, DELIVERED, FAILED, READ
    sent_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<NotificationLog(user_id='{self.user_id}', channel='{self.channel}', status='{self.status}')>"
