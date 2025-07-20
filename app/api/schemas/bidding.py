from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator
from app.api.schemas.base import ResponseSchema


class BidCreate(BaseModel):
    """Schema for creating a bid"""
    commodity_listing_id: UUID = Field(..., description="ID of the commodity listing")
    amount: Decimal = Field(..., gt=0, description="Bid amount in rupees")
    message: Optional[str] = Field(None, max_length=500, description="Optional message with the bid")
    expires_in_minutes: Optional[int] = Field(60, ge=1, le=1440, description="Bid expiration in minutes (1-1440)")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Bid amount must be positive')
        # Round to 2 decimal places
        return round(v, 2)


class BidResponse(BaseModel):
    """Schema for bid responses"""
    id: UUID
    commodity_listing_id: UUID
    user_id: UUID  # Changed from bidder_id to match model
    amount: Decimal
    status: str
    message: Optional[str] = None
    bid_time: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BidResponseSchema(ResponseSchema):
    """Response schema for single bid"""
    data: BidResponse


class AuctionRoomResponse(BaseModel):
    """Schema for bid response"""
    id: UUID
    commodity_listing_id: UUID
    bidder_id: UUID
    bidder_name: str
    amount: Decimal
    message: Optional[str]
    status: str
    bid_time: datetime
    expires_at: Optional[datetime]
    is_highest: bool = False
    
    class Config:
        from_attributes = True


class BidUpdate(BaseModel):
    """Schema for updating bid status"""
    action: str = Field(..., description="Action to perform: withdraw, accept, reject")


class AuctionRoomResponse(BaseModel):
    """Schema for auction room response"""
    commodity_listing_id: UUID
    commodity_title: str
    commodity_farmer: str
    current_highest_bid: Optional[Decimal]
    current_highest_bidder: Optional[str]
    total_bids: int
    active_participants: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuctionRoomResponseSchema(ResponseSchema):
    """Response schema for single auction room"""
    data: AuctionRoomResponse
    
    class Config:
        from_attributes = True


class AuctionRoomDetail(BaseModel):
    """Detailed auction room information"""
    room_info: AuctionRoomResponse
    recent_bids: List[BidResponse]
    participant_count: int
    time_remaining: Optional[str]


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str = Field(..., description="Message type: new_bid, bid_update, user_joined, user_left")
    data: dict = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NewBidMessage(BaseModel):
    """Schema for new bid WebSocket message"""
    bid_id: UUID
    commodity_id: UUID
    bidder_name: str
    amount: Decimal
    timestamp: datetime
    message: Optional[str]


class BidUpdateMessage(BaseModel):
    """Schema for bid update WebSocket message"""
    bid_id: UUID
    commodity_id: UUID
    action: str  # withdrawn, accepted, rejected
    timestamp: datetime


class UserActivityMessage(BaseModel):
    """Schema for user activity WebSocket message"""
    user_name: str
    action: str  # joined, left
    participant_count: int
    timestamp: datetime


class BidListResponse(ResponseSchema):
    """Response schema for bid lists"""
    data: List[BidResponse]


class AuctionRoomListResponse(ResponseSchema):
    """Response schema for auction room lists"""
    data: List[AuctionRoomResponse]


class BidStatsResponse(BaseModel):
    """Schema for bid statistics"""
    total_bids: int
    active_bids: int
    accepted_bids: int
    withdrawn_bids: int
    average_bid_amount: Optional[Decimal]
    highest_bid_amount: Optional[Decimal]
    most_active_commodity: Optional[str]


class BidStatsResponseSchema(ResponseSchema):
    """Response schema for bid statistics"""
    data: BidStatsResponse


class AuctionParticipantResponse(BaseModel):
    """Schema for auction participant info"""
    user_id: UUID
    user_name: str
    bid_count: int
    highest_bid: Optional[Decimal]
    is_online: bool
