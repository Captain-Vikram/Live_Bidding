from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Numeric,
    Date,
    Float,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship, validates
import enum

from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as GUUID  # General UUID

from app.db.models.accounts import User

from .base import BaseModel, File
from datetime import datetime


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = Column(String(30), unique=True)
    slug: Mapped[str] = Column(String(), unique=True)

    def __repr__(self):
        return self.name

    @validates("name")
    def validate_name(self, key, value):
        if value == "Other":
            raise ValueError("Name must not be 'Other'")
        return value


# Agricultural commodity listing model
class CommodityListing(BaseModel):
    __tablename__ = "commodity_listings"

    farmer_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    farmer: Mapped[User] = relationship("User", lazy="joined")

    commodity_name: Mapped[str] = Column(String(100))
    slug: Mapped[str] = Column(String(), unique=True)
    description: Mapped[str] = Column(Text(), nullable=True)
    
    quantity_kg: Mapped[float] = Column(Float())
    harvest_date: Mapped[datetime] = Column(Date())
    min_price: Mapped[float] = Column(Numeric(precision=10, scale=2))
    
    # Current highest bid
    highest_bid: Mapped[float] = Column(Numeric(precision=10, scale=2), default=0.00)
    bids_count: Mapped[int] = Column(Integer, default=0)
    
    # Status fields
    is_approved: Mapped[bool] = Column(Boolean(), default=False)
    is_active: Mapped[bool] = Column(Boolean(), default=True)
    closing_date: Mapped[datetime] = Column(DateTime, nullable=True)

    category_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[Category] = relationship("Category", lazy="joined")

    image_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        unique=True,
    )
    image: Mapped[File] = relationship("File", lazy="joined")

    def __repr__(self):
        return f"{self.commodity_name} - {self.quantity_kg}kg"

    @property
    def time_left_seconds(self):
        if not self.closing_date:
            return None
        remaining_time = self.closing_date - datetime.utcnow()
        remaining_seconds = remaining_time.total_seconds()
        return remaining_seconds

    @property
    def time_left(self):
        if not self.is_active or not self.closing_date:
            return 0
        return self.time_left_seconds


class Listing(BaseModel):
    __tablename__ = "listings"

    auctioneer_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    auctioneer: Mapped[User] = relationship("User", lazy="joined")

    name: Mapped[str] = Column(String(70))
    slug: Mapped[str] = Column(String(), unique=True)
    desc: Mapped[str] = Column(Text())

    category_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[Category] = relationship("Category", lazy="joined")

    price: Mapped[float] = Column(Numeric(precision=10, scale=2))
    highest_bid: Mapped[float] = Column(Numeric(precision=10, scale=2), default=0.00)
    bids_count: Mapped[int] = Column(Integer, default=0)
    closing_date: Mapped[datetime] = Column(DateTime, nullable=True)
    active: Mapped[bool] = Column(Boolean, default=True)

    image_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="SET NULL"),
        unique=True,
    )
    image: Mapped[File] = relationship("File", lazy="joined")

    def __repr__(self):
        return self.name

    @property
    def time_left_seconds(self):
        remaining_time = self.closing_date - datetime.utcnow()
        remaining_seconds = remaining_time.total_seconds()
        return remaining_seconds

    @property
    def time_left(self):
        if not self.active:
            return 0
        return self.time_left_seconds


import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, DateTime, UniqueConstraint, Numeric, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from app.db.models.base import BaseModel
from app.db.models.accounts import User


class BidStatus(enum.Enum):
    """Enum for bid status"""
    ACTIVE = "active"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class Bid(BaseModel):
    __tablename__ = "bids"

    user_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship("User", lazy="joined")

    # Support both old listings and new commodity listings
    listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=True
    )
    listing: Mapped[Listing] = relationship("Listing", lazy="joined")
    
    commodity_listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("commodity_listings.id", ondelete="CASCADE"), nullable=True
    )
    commodity_listing: Mapped[CommodityListing] = relationship("CommodityListing", lazy="joined")
    
    amount: Mapped[float] = Column(Numeric(precision=10, scale=2))
    
    # Real-time bidding features
    message: Mapped[str] = Column(Text, nullable=True)
    status: Mapped[BidStatus] = Column(SQLEnum(BidStatus), default=BidStatus.ACTIVE, nullable=False)
    bid_time: Mapped[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    # Add property aliases for consistency
    @property
    def bidder(self):
        return self.user
    
    @property
    def bidder_id(self):
        return self.user_id
    
    def __repr__(self):
        if self.listing:
            return f"{self.listing.name} - ₹{self.amount} ({self.status.value})"
        elif self.commodity_listing:
            return f"{self.commodity_listing.commodity_name} - ₹{self.amount} ({self.status.value})"
        return f"Bid - ₹{self.amount} ({self.status.value})"

    __table_args__ = (
        UniqueConstraint("listing_id", "amount", name="unique_listing_amount_bids"),
        UniqueConstraint("commodity_listing_id", "amount", name="unique_commodity_listing_amount_bids"),
        Index("idx_bids_commodity_status", "commodity_listing_id", "status"),
        Index("idx_bids_user_status", "user_id", "status"),
        Index("idx_bids_bid_time", "bid_time"),
    )


class AuctionRoom(BaseModel):
    """Model for real-time auction rooms"""
    __tablename__ = "auction_rooms"
    
    commodity_listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("commodity_listings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    commodity_listing: Mapped[CommodityListing] = relationship("CommodityListing", lazy="joined")
    
    current_highest_bid: Mapped[float] = Column(Numeric(precision=10, scale=2), nullable=True)
    current_highest_bidder_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    current_highest_bidder: Mapped[User] = relationship("User", lazy="joined")
    
    total_bids: Mapped[int] = Column(Integer, default=0)
    active_participants: Mapped[int] = Column(Integer, default=0)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"AuctionRoom - {self.commodity_listing.commodity_name} (₹{self.current_highest_bid or 0})"

    __table_args__ = (
        Index("idx_auction_rooms_active", "is_active"),
        Index("idx_auction_rooms_bids", "total_bids"),
    )


class WatchList(BaseModel):
    __tablename__ = "watchlists"

    user_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped[User] = relationship("User", lazy="joined")

    # Support both old listings and new commodity listings
    listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=True
    )
    listing: Mapped[Listing] = relationship("Listing", lazy="joined")
    
    commodity_listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("commodity_listings.id", ondelete="CASCADE"), nullable=True
    )
    commodity_listing: Mapped[CommodityListing] = relationship("CommodityListing", lazy="joined")

    session_key: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("guestusers.id", ondelete="CASCADE")
    )

    def __repr__(self):
        if self.user:
            if self.listing:
                return f"{self.listing.name} - {self.user.full_name}"
            elif self.commodity_listing:
                return f"{self.commodity_listing.commodity_name} - {self.user.full_name}"
        return f"Watchlist - {self.session_key}"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "listing_id", name="unique_user_listing_watchlists"
        ),
        UniqueConstraint(
            "user_id", "commodity_listing_id", name="unique_user_commodity_listing_watchlists"
        ),
        UniqueConstraint(
            "session_key",
            "listing_id",
            name="unique_session_key_listing_watchlists",
        ),
        UniqueConstraint(
            "session_key",
            "commodity_listing_id",
            name="unique_session_key_commodity_listing_watchlists",
        ),
    )
