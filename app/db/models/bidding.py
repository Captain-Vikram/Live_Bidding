from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Numeric,
    Boolean,
    Text,
    Enum,
)
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import UUID as GUUID
import enum
from datetime import datetime

from .base import BaseModel
from .accounts import User
from .listings import CommodityListing


class BidStatus(enum.Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Bid(BaseModel):
    __tablename__ = "bids"

    commodity_listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("commodity_listings.id", ondelete="CASCADE")
    )
    commodity_listing: Mapped[CommodityListing] = relationship("CommodityListing", lazy="joined")
    
    bidder_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    bidder: Mapped[User] = relationship("User", lazy="joined")
    
    amount: Mapped[float] = Column(Numeric(precision=10, scale=2))
    message: Mapped[str] = Column(Text(), nullable=True)  # Optional message from bidder
    
    status: Mapped[BidStatus] = Column(Enum(BidStatus), default=BidStatus.ACTIVE)
    is_auto_bid: Mapped[bool] = Column(Boolean(), default=False)  # For automatic bidding
    
    # Timestamps
    bid_time: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"Bid(₹{self.amount} by {self.bidder.full_name} for {self.commodity_listing.commodity_name})"

    @property
    def is_valid(self):
        """Check if bid is still valid"""
        if self.status != BidStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True


class AuctionRoom(BaseModel):
    __tablename__ = "auction_rooms"

    commodity_listing_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("commodity_listings.id", ondelete="CASCADE"), unique=True
    )
    commodity_listing: Mapped[CommodityListing] = relationship("CommodityListing", lazy="joined")
    
    is_active: Mapped[bool] = Column(Boolean(), default=True)
    start_time: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    end_time: Mapped[datetime] = Column(DateTime, nullable=True)
    
    # Current auction state
    current_highest_bid: Mapped[float] = Column(Numeric(precision=10, scale=2), nullable=True)
    current_highest_bidder_id: Mapped[GUUID] = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    current_highest_bidder: Mapped[User] = relationship("User", lazy="joined")
    
    total_bids: Mapped[int] = Column(default=0)
    active_participants: Mapped[int] = Column(default=0)

    def __repr__(self):
        return f"AuctionRoom({self.commodity_listing.commodity_name} - ₹{self.current_highest_bid})"
