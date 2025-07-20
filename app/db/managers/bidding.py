from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, and_, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timedelta
import json

from app.db.models.listings import Bid, AuctionRoom, BidStatus, CommodityListing
from app.db.models.accounts import User
from app.core.redis import redis_manager
from .base import BaseManager


class BidManager(BaseManager[Bid]):
    """Manager for bid operations"""

    async def create_bid(
        self,
        db: AsyncSession,
        commodity_listing_id: UUID,
        bidder_id: UUID,
        amount: float,
        message: Optional[str] = None,
        expires_in_minutes: int = 60
    ) -> Bid:
        """Create a new bid"""
        
        # Check if commodity listing exists and is active
        commodity_query = select(CommodityListing).where(
            and_(
                CommodityListing.id == commodity_listing_id,
                CommodityListing.is_active == True,
                CommodityListing.is_approved == True
            )
        )
        commodity = await db.scalar(commodity_query)
        
        if not commodity:
            raise ValueError("Commodity listing not found or not available for bidding")
        
        # Check if bid amount is valid (must be higher than minimum price and current highest bid)
        if amount < commodity.min_price:
            raise ValueError(f"Bid amount must be at least ₹{commodity.min_price}")
        
        if commodity.highest_bid and amount <= commodity.highest_bid:
            raise ValueError(f"Bid amount must be higher than current highest bid of ₹{commodity.highest_bid}")
        
        # Check if bidder is not the commodity owner
        if commodity.farmer_id == bidder_id:
            raise ValueError("You cannot bid on your own commodity")
        
        # Create bid
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        bid_data = {
            "commodity_listing_id": commodity_listing_id,
            "user_id": bidder_id,
            "amount": amount,
            "message": message,
            "expires_at": expires_at,
            "status": BidStatus.ACTIVE
        }
        
        bid = Bid(**bid_data)
        db.add(bid)
        await db.flush()
        
        # Update commodity highest bid
        await db.execute(
            update(CommodityListing)
            .where(CommodityListing.id == commodity_listing_id)
            .values(
                highest_bid=amount,
                bids_count=CommodityListing.bids_count + 1
            )
        )
        
        # Update or create auction room
        await self._update_auction_room(db, commodity_listing_id, amount, bidder_id)
        
        await db.commit()
        await db.refresh(bid)
        
        # Broadcast bid to auction room
        await self._broadcast_bid(bid)
        
        return bid

    async def get_bids_for_commodity(
        self,
        db: AsyncSession,
        commodity_listing_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Bid]:
        """Get bids for a specific commodity"""
        
        query = (
            select(Bid)
            .where(Bid.commodity_listing_id == commodity_listing_id)
            .options(selectinload(Bid.bidder))
            .order_by(desc(Bid.amount), desc(Bid.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_bids(
        self,
        db: AsyncSession,
        user_id: UUID,
        status: Optional[BidStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Bid]:
        """Get bids made by a specific user"""
        
        query = (
            select(Bid)
            .where(Bid.bidder_id == user_id)
            .options(selectinload(Bid.commodity_listing))
        )
        
        if status:
            query = query.where(Bid.status == status)
        
        query = query.order_by(desc(Bid.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def withdraw_bid(self, db: AsyncSession, bid_id: UUID, user_id: UUID) -> Bid:
        """Withdraw a bid"""
        
        query = select(Bid).where(
            and_(
                Bid.id == bid_id,
                Bid.bidder_id == user_id,
                Bid.status == BidStatus.ACTIVE
            )
        )
        
        bid = await db.scalar(query)
        if not bid:
            raise ValueError("Bid not found or cannot be withdrawn")
        
        bid.status = BidStatus.WITHDRAWN
        await db.commit()
        
        # Broadcast withdrawal
        await self._broadcast_bid_update(bid, "withdrawn")
        
        return bid

    async def accept_bid(self, db: AsyncSession, bid_id: UUID, farmer_id: UUID) -> Bid:
        """Accept a bid (farmer only)"""
        
        query = (
            select(Bid)
            .options(selectinload(Bid.commodity_listing))
            .where(
                and_(
                    Bid.id == bid_id,
                    Bid.status == BidStatus.ACTIVE
                )
            )
        )
        
        bid = await db.scalar(query)
        if not bid:
            raise ValueError("Bid not found or not active")
        
        if bid.commodity_listing.farmer_id != farmer_id:
            raise ValueError("Only the commodity owner can accept bids")
        
        # Accept this bid and reject all others for this commodity
        await db.execute(
            update(Bid)
            .where(
                and_(
                    Bid.commodity_listing_id == bid.commodity_listing_id,
                    Bid.status == BidStatus.ACTIVE,
                    Bid.id != bid_id
                )
            )
            .values(status=BidStatus.REJECTED)
        )
        
        bid.status = BidStatus.ACCEPTED
        
        # Mark commodity as sold/inactive
        await db.execute(
            update(CommodityListing)
            .where(CommodityListing.id == bid.commodity_listing_id)
            .values(is_active=False)
        )
        
        await db.commit()
        
        # Broadcast acceptance
        await self._broadcast_bid_update(bid, "accepted")
        
        return bid

    async def get_auction_room(self, db: AsyncSession, commodity_listing_id: UUID) -> Optional[AuctionRoom]:
        """Get auction room for commodity"""
        
        query = (
            select(AuctionRoom)
            .options(
                selectinload(AuctionRoom.commodity_listing),
                selectinload(AuctionRoom.current_highest_bidder)
            )
            .where(AuctionRoom.commodity_listing_id == commodity_listing_id)
        )
        
        return await db.scalar(query)

    async def get_active_auction_rooms(self, db: AsyncSession, limit: int = 20) -> List[AuctionRoom]:
        """Get active auction rooms"""
        
        query = (
            select(AuctionRoom)
            .options(selectinload(AuctionRoom.commodity_listing))
            .where(AuctionRoom.is_active == True)
            .order_by(desc(AuctionRoom.total_bids))
            .limit(limit)
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def _update_auction_room(
        self,
        db: AsyncSession,
        commodity_listing_id: UUID,
        bid_amount: float,
        bidder_id: UUID
    ):
        """Update or create auction room"""
        
        # Check if auction room exists
        auction_room = await db.scalar(
            select(AuctionRoom).where(AuctionRoom.commodity_listing_id == commodity_listing_id)
        )
        
        if auction_room:
            # Update existing room
            auction_room.current_highest_bid = bid_amount
            auction_room.current_highest_bidder_id = bidder_id
            auction_room.total_bids += 1
        else:
            # Create new auction room
            auction_room = AuctionRoom(
                commodity_listing_id=commodity_listing_id,
                current_highest_bid=bid_amount,
                current_highest_bidder_id=bidder_id,
                total_bids=1,
                active_participants=1
            )
            db.add(auction_room)

    async def _broadcast_bid(self, bid: Bid):
        """Broadcast new bid to WebSocket clients"""
        
        message = {
            "type": "new_bid",
            "data": {
                "bid_id": str(bid.id),
                "commodity_id": str(bid.commodity_listing_id),
                "bidder_name": bid.bidder.first_name,  # Don't expose full details
                "amount": float(bid.amount),
                "timestamp": bid.bid_time.isoformat(),
                "message": bid.message
            }
        }
        
        channel = f"auction:{bid.commodity_listing_id}"
        await redis_manager.publish(channel, message)

    async def _broadcast_bid_update(self, bid: Bid, action: str):
        """Broadcast bid status update"""
        
        message = {
            "type": "bid_update",
            "data": {
                "bid_id": str(bid.id),
                "commodity_id": str(bid.commodity_listing_id),
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        channel = f"auction:{bid.commodity_listing_id}"
        await redis_manager.publish(channel, message)


# Global instance
bid_manager = BidManager(Bid)
