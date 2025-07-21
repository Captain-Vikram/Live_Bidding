from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from app.api.schemas.base import ResponseSchema


class UserRole(str, Enum):
    """User role enumeration"""
    FARMER = "FARMER"
    TRADER = "TRADER"
    ADMIN = "ADMIN"


class UserListItem(BaseModel):
    """User list item for admin interface"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserDetail(BaseModel):
    """Detailed user information for admin"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    phone_number: Optional[str] = None
    profile_picture: Optional[str] = None
    address: Optional[str] = None
    total_listings: int = 0
    total_bids: int = 0
    total_purchases: int = 0
    
    class Config:
        from_attributes = True


class UserVerificationUpdate(BaseModel):
    """Schema for updating user verification status"""
    is_verified: bool = Field(..., description="Verification status")
    verification_notes: Optional[str] = Field(None, description="Admin notes for verification")


class UserListResponse(ResponseSchema):
    """Response schema for user list"""
    data: List[UserListItem]
    total_count: int
    page: int
    page_size: int


class UserDetailResponse(ResponseSchema):
    """Response schema for user details"""
    data: UserDetail


class UserVerificationResponse(ResponseSchema):
    """Response schema for user verification update"""
    data: Dict[str, Any]


class PlatformStats(BaseModel):
    """Platform statistics for admin dashboard"""
    total_users: int
    active_users: int
    verified_users: int
    total_listings: int
    active_listings: int
    pending_approval_listings: int
    total_bids: int
    active_auctions: int
    total_revenue: float
    monthly_revenue: float
    total_transactions: int
    monthly_transactions: int


class ActiveBidsStats(BaseModel):
    """Active bids statistics"""
    total_active_auctions: int
    total_active_bids: int
    highest_bid_amount: float
    average_bid_amount: float
    auctions_ending_today: int
    auctions_ending_this_week: int


class CommoditiesStats(BaseModel):
    """Commodities statistics"""
    total_commodities: int
    active_commodities: int
    pending_approval: int
    categories_count: int
    most_popular_category: str
    average_commodity_price: float


class PlatformStatsResponse(ResponseSchema):
    """Response schema for platform statistics"""
    data: PlatformStats


class ActiveBidsStatsResponse(ResponseSchema):
    """Response schema for active bids statistics"""
    data: ActiveBidsStats


class CommoditiesStatsResponse(ResponseSchema):
    """Response schema for commodities statistics"""
    data: CommoditiesStats


class DeleteUserResponse(ResponseSchema):
    """Response schema for user deletion"""
    data: Dict[str, Any]
