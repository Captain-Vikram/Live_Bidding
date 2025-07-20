"""
Price Tracking API Schemas
===========================

Pydantic models for price tracking and alert endpoints
"""

from datetime import date, datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from uuid import UUID

from app.api.schemas.base import BaseAPISchema


class AlertDirection(str, Enum):
    """Alert direction enumeration"""
    BUY = "buy"
    SELL = "sell"


class PriceHistoryBase(BaseModel):
    """Base price history schema"""
    commodity_id: UUID
    date: date
    avg_price: float = Field(..., gt=0, description="Average price for the day")
    high_price: float = Field(..., gt=0, description="Highest price for the day")
    low_price: float = Field(..., gt=0, description="Lowest price for the day")
    volume_kg: float = Field(default=0.0, ge=0, description="Volume traded in kg")
    market_name: Optional[str] = Field(None, description="Market or location name")
    source: str = Field(default="manual", description="Data source (manual, api, etc.)")
    
    @validator('high_price')
    def high_price_validation(cls, v, values):
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('High price cannot be less than low price')
        return v
    
    @validator('avg_price')
    def avg_price_validation(cls, v, values):
        if 'low_price' in values and 'high_price' in values:
            if v < values['low_price'] or v > values['high_price']:
                raise ValueError('Average price must be between low and high price')
        return v


class PriceHistoryCreate(PriceHistoryBase):
    """Schema for creating price history"""
    pass


class PriceHistoryUpdate(BaseModel):
    """Schema for updating price history"""
    avg_price: Optional[float] = Field(None, gt=0)
    high_price: Optional[float] = Field(None, gt=0)
    low_price: Optional[float] = Field(None, gt=0)
    volume_kg: Optional[float] = Field(None, ge=0)
    market_name: Optional[str] = None
    source: Optional[str] = None


class PriceHistoryResponse(PriceHistoryBase, BaseAPISchema):
    """Schema for price history response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PriceStatistics(BaseModel):
    """Price statistics for a commodity"""
    period_days: int
    current_price: Optional[float]
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    total_volume: float
    data_points: int
    price_change: Optional[float]
    price_change_pct: Optional[float]
    last_updated: Optional[date]


class TrendingCommodity(BaseModel):
    """Trending commodity with price change"""
    commodity_id: str
    commodity_name: str
    current_price: Optional[float]
    price_change_pct: float
    avg_price_7d: Optional[float]


class AlertSubscriptionBase(BaseModel):
    """Base alert subscription schema"""
    commodity_id: UUID
    threshold_price: Optional[float] = Field(None, gt=0, description="Price threshold for alert")
    threshold_pct: Optional[float] = Field(None, description="Percentage change threshold")
    direction: AlertDirection = Field(AlertDirection.BUY, description="Alert direction")
    notify_email: bool = Field(True, description="Send email notifications")
    notify_sms: bool = Field(False, description="Send SMS notifications")
    notify_push: bool = Field(True, description="Send push notifications")
    
    @validator('threshold_pct')
    def threshold_pct_validation(cls, v):
        if v is not None and (v < -100 or v > 1000):
            raise ValueError('Percentage threshold must be between -100% and 1000%')
        return v
    
    @validator('threshold_price', 'threshold_pct')
    def at_least_one_threshold(cls, v, values, field):
        if field.name == 'threshold_pct':
            threshold_price = values.get('threshold_price')
            if not threshold_price and not v:
                raise ValueError('Either threshold_price or threshold_pct must be provided')
        return v


class AlertSubscriptionCreate(AlertSubscriptionBase):
    """Schema for creating alert subscription"""
    pass


class AlertSubscriptionUpdate(BaseModel):
    """Schema for updating alert subscription"""
    threshold_price: Optional[float] = Field(None, gt=0)
    threshold_pct: Optional[float] = None
    direction: Optional[AlertDirection] = None
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_push: Optional[bool] = None
    is_active: Optional[bool] = None


class AlertSubscriptionResponse(AlertSubscriptionBase, BaseAPISchema):
    """Schema for alert subscription response"""
    id: UUID
    user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_triggered: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PriceAlertBase(BaseModel):
    """Base price alert schema"""
    user_id: UUID
    commodity_id: UUID
    subscription_id: UUID
    alert_price: float = Field(..., gt=0)
    threshold_type: str = Field(..., description="Type of threshold (price/percentage)")
    threshold_value: float = Field(..., description="The threshold value that triggered the alert")
    message: str = Field(..., description="Alert message")
    sent_email: bool = Field(default=False)
    sent_sms: bool = Field(default=False)
    sent_push: bool = Field(default=False)


class PriceAlertResponse(PriceAlertBase, BaseAPISchema):
    """Schema for price alert response"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class BulkPriceImport(BaseModel):
    """Schema for bulk price data import"""
    commodity_id: UUID
    price_data: List[PriceHistoryCreate]
    
    @validator('price_data')
    def validate_price_data(cls, v):
        if len(v) == 0:
            raise ValueError('At least one price record is required')
        if len(v) > 1000:
            raise ValueError('Maximum 1000 price records per bulk import')
        return v


class PriceHistoryQuery(BaseModel):
    """Schema for price history query parameters"""
    commodity_id: UUID
    days: Optional[int] = Field(30, ge=1, le=365, description="Number of days to retrieve")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    @validator('end_date')
    def end_date_validation(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date cannot be before start date')
        return v


class MarketPriceUpdate(BaseModel):
    """Schema for external market price updates"""
    source: str = Field(..., description="Data source name")
    prices: List[PriceHistoryCreate]
    
    @validator('prices')
    def validate_prices(cls, v):
        if len(v) == 0:
            raise ValueError('At least one price update is required')
        return v


# Response schemas for lists
class PriceHistoryListResponse(BaseModel):
    """Response schema for price history list"""
    items: List[PriceHistoryResponse]
    total: int
    page: int = 1
    page_size: int = 50


class AlertSubscriptionListResponse(BaseModel):
    """Response schema for alert subscription list"""
    items: List[AlertSubscriptionResponse]
    total: int
    page: int = 1
    page_size: int = 50


class PriceAlertListResponse(BaseModel):
    """Response schema for price alert list"""
    items: List[PriceAlertResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ENHANCED SCHEMAS FOR PHASE 5

from decimal import Decimal
from app.api.schemas.base import ResponseSchema

class TrendDirectionEnum(str, Enum):
    """Trend direction enumeration"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    STRONG_UP = "strong_up"
    STRONG_DOWN = "strong_down"

class OnSiteNotificationCreate(BaseModel):
    """Schema for creating on-site notifications"""
    title: str = Field(..., max_length=200, description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(..., description="Type of notification (PRICE_ALERT, BID_UPDATE, etc.)")
    is_urgent: bool = Field(default=False, description="Whether notification is urgent")
    extra_data: Optional[str] = Field(None, description="Additional data as JSON string")
    action_url: Optional[str] = Field(None, description="URL for action button")

class OnSiteNotificationResponse(BaseModel):
    """Schema for on-site notification response"""
    id: UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    is_urgent: bool
    read_at: Optional[datetime]
    expires_at: Optional[datetime]
    extra_data: Optional[str]
    action_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class OnSiteNotificationListResponse(BaseModel):
    """Response schema for on-site notification list"""
    notifications: List[OnSiteNotificationResponse]
    unread_count: int
    total_count: int

class NotificationMarkReadRequest(BaseModel):
    """Schema for marking notifications as read"""
    notification_ids: List[UUID] = Field(..., description="List of notification IDs to mark as read")

class PriceStatisticsResponse(BaseModel):
    """Schema for price statistics"""
    commodity_name: str
    period_days: int
    avg_price: Decimal = Field(..., decimal_places=2)
    min_price: Decimal = Field(..., decimal_places=2)
    max_price: Decimal = Field(..., decimal_places=2)
    price_volatility: Decimal = Field(..., decimal_places=2)
    total_volume: Decimal = Field(..., decimal_places=2)
    data_points: int
    trend_direction: TrendDirectionEnum
    price_change_pct: Decimal = Field(..., decimal_places=2)

class TrendingCommodityResponse(BaseModel):
    """Schema for trending commodity data"""
    commodity_id: UUID
    commodity_name: str
    current_price: Decimal = Field(..., decimal_places=2)
    previous_price: Decimal = Field(..., decimal_places=2)
    price_change_pct: Decimal = Field(..., decimal_places=2)
    trend: TrendDirectionEnum
    volume_change_pct: Optional[Decimal] = Field(None, decimal_places=2)

class DashboardSummaryResponse(BaseModel):
    """Schema for dashboard summary data"""
    total_commodities_tracked: int
    total_active_alerts: int
    price_changes_today: int
    alerts_triggered_today: int
    trending_up: List[str]
    trending_down: List[str]
    recent_notifications: List[OnSiteNotificationResponse]

# Enhanced alert subscription schemas
class AlertSubscriptionCreateEnhanced(BaseModel):
    """Enhanced schema for creating alert subscriptions"""
    commodity_id: UUID = Field(..., description="Commodity to watch")
    threshold_price: Decimal = Field(..., decimal_places=2, description="Price threshold for alert")
    direction: AlertDirection = Field(..., description="Alert direction (buy/sell)")
    threshold_pct: Optional[Decimal] = Field(None, decimal_places=2, description="Percentage change threshold")
    
    # Enhanced notification preferences
    notify_email: bool = Field(default=True, description="Send email notifications")
    notify_sms: bool = Field(default=False, description="Send SMS notifications")
    notify_push: bool = Field(default=True, description="Send push notifications")
    notify_onsite: bool = Field(default=True, description="Send on-site notifications")
    
    max_triggers_per_day: int = Field(default=3, ge=1, le=10, description="Maximum alerts per day")

class AlertSubscriptionResponseEnhanced(BaseModel):
    """Enhanced schema for alert subscription response"""
    id: UUID
    user_id: UUID
    commodity_id: UUID
    commodity_name: str
    threshold_price: Decimal = Field(..., decimal_places=2)
    direction: AlertDirection
    threshold_pct: Optional[Decimal] = Field(None, decimal_places=2)
    
    # Notification preferences
    notify_email: bool
    notify_sms: bool
    notify_push: bool
    notify_onsite: bool
    
    # Status
    is_active: bool
    last_triggered: Optional[datetime]
    trigger_count_today: int
    max_triggers_per_day: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
