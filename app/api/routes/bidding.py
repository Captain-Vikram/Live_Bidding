from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.utils.auth import get_current_user
from app.api.middleware import require_verified_user
from app.db.models.accounts import User, UserRole
from app.db.models.listings import BidStatus
from app.db.managers.bidding import bid_manager
from app.db.managers.listings import listing_manager
from app.db.models.listings import BidStatus
from app.api.schemas.bidding import (
    BidCreate, BidResponseSchema, BidResponse, BidUpdate, BidListResponse,
    AuctionRoomResponseSchema, AuctionRoomResponse, AuctionRoomListResponse, 
    BidStatsResponseSchema, BidStatsResponse
)
from app.api.schemas.base import ResponseSchema
from app.api.utils.notifications import send_bid_notification, send_outbid_alert

router = APIRouter()


@router.post("/bids", response_model=BidResponseSchema)
async def create_bid(
    bid_data: BidCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_verified_user)  # ✅ Now enforces KYC verification
):
    """Create a new bid on a commodity"""
    
    # Only traders can place bids
    if current_user.role != UserRole.TRADER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only traders can place bids"
        )
    
    try:
        # Get commodity listing details for notifications
        listing = await listing_manager.get(db=db, id=bid_data.commodity_listing_id)
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commodity listing not found"
            )
        
        bid = await bid_manager.create_bid(
            db=db,
            commodity_listing_id=bid_data.commodity_listing_id,
            bidder_id=current_user.id,
            amount=float(bid_data.amount),
            message=bid_data.message,
            expires_in_minutes=bid_data.expires_in_minutes or 60
        )
        
        # Send bid confirmation notification
        try:
            product_name = f"{listing.commodity_name} ({listing.quantity}kg)"
            auction_url = f"https://agritech.com/auction/{listing.id}"
            
            await send_bid_notification(
                db=db,
                user_id=current_user.id,
                product_name=product_name,
                amount=float(bid_data.amount),
                status="confirmed",
                url=auction_url,
                background_tasks=background_tasks
            )
        except Exception as e:
            # Log notification error but don't fail the bid
            print(f"Notification error: {e}")
        
        # Create response dict from bid
        bid_dict = {
            "id": bid.id,
            "commodity_listing_id": bid.commodity_listing_id,
            "user_id": bid.user_id,
            "amount": bid.amount,
            "status": bid.status.value,  # Convert enum to string
            "message": bid.message,
            "bid_time": bid.bid_time,
            "expires_at": bid.expires_at,
            "created_at": bid.created_at,
            "updated_at": bid.updated_at
        }
        
        return BidResponseSchema(
            status="success",
            message="Bid placed successfully",
            data=bid_dict
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create bid")


@router.get("/bids/my-bids", response_model=BidListResponse)
async def get_my_bids(
    status_filter: Optional[str] = Query(None, description="Filter by bid status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's bids"""
    
    # Convert status filter
    bid_status = None
    if status_filter:
        try:
            bid_status = BidStatus(status_filter.upper())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    
    bids = await bid_manager.get_user_bids(
        db=db,
        user_id=current_user.id,
        status=bid_status,
        limit=limit,
        offset=offset
    )
    
    bid_responses = []
    for bid in bids:
        bid_response = BidResponse(
            id=bid.id,
            commodity_listing_id=bid.commodity_listing_id,
            bidder_id=bid.bidder_id,
            bidder_name=f"{current_user.first_name} {current_user.last_name}",
            amount=bid.amount,
            message=bid.message,
            status=bid.status.value,
            bid_time=bid.bid_time,
            expires_at=bid.expires_at,
            is_highest=(bid.commodity_listing.highest_bid == bid.amount) if bid.commodity_listing else False
        )
        bid_responses.append(bid_response)
    
    return BidListResponse(
        success=True,
        message="User bids retrieved successfully",
        data=bid_responses
    )


@router.get("/bids/commodity/{commodity_id}", response_model=BidListResponse)
async def get_commodity_bids(
    commodity_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bids for a specific commodity"""
    
    # Verify commodity exists
    commodity = await listing_manager.get_by_id(db, commodity_id)
    if not commodity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commodity not found")
    
    # Check permissions - farmers can see all bids on their commodities, traders can see all bids
    if current_user.role == UserRole.FARMER and commodity.farmer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view bids on your own commodities"
        )
    
    bids = await bid_manager.get_bids_for_commodity(
        db=db,
        commodity_listing_id=commodity_id,
        limit=limit,
        offset=offset
    )
    
    bid_responses = []
    highest_bid = commodity.highest_bid
    
    for bid in bids:
        bid_response = BidResponse(
            id=bid.id,
            commodity_listing_id=bid.commodity_listing_id,
            bidder_id=bid.bidder_id,
            bidder_name=f"{bid.bidder.first_name} {bid.bidder.last_name}",
            amount=bid.amount,
            message=bid.message,
            status=bid.status.value,
            bid_time=bid.bid_time,
            expires_at=bid.expires_at,
            is_highest=(bid.amount == highest_bid)
        )
        bid_responses.append(bid_response)
    
    return BidListResponse(
        success=True,
        message="Commodity bids retrieved successfully",
        data=bid_responses
    )


@router.patch("/bids/{bid_id}", response_model=BidResponseSchema)
async def update_bid(
    bid_id: UUID,
    bid_update: BidUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_verified_user)  # ✅ Requires KYC for bid modifications
):
    """Update bid status (withdraw, accept, reject)"""
    
    try:
        if bid_update.action == "withdraw":
            bid = await bid_manager.withdraw_bid(db, bid_id, current_user.id)
        elif bid_update.action == "accept":
            # Only farmers can accept bids
            if current_user.role != UserRole.FARMER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only farmers can accept bids"
                )
            bid = await bid_manager.accept_bid(db, bid_id, current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use 'withdraw' or 'accept'"
            )
        
        bid_response = BidResponse(
            id=bid.id,
            commodity_listing_id=bid.commodity_listing_id,
            bidder_id=bid.bidder_id,
            bidder_name=f"{bid.bidder.first_name} {bid.bidder.last_name}",
            amount=bid.amount,
            message=bid.message,
            status=bid.status.value,
            bid_time=bid.bid_time,
            expires_at=bid.expires_at,
            is_highest=False
        )
        
        return BidResponseSchema(
            status="success",
            message=f"Bid {bid_update.action}ed successfully",
            data=bid_response
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update bid")


@router.get("/auction-rooms", response_model=AuctionRoomListResponse)
async def get_auction_rooms(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active auction rooms"""
    
    rooms = await bid_manager.get_active_auction_rooms(db, limit)
    
    room_responses = []
    for room in rooms:
        room_response = AuctionRoomResponse(
            commodity_listing_id=room.commodity_listing_id,
            commodity_title=room.commodity_listing.commodity_name,
            commodity_farmer=f"{room.commodity_listing.farmer.first_name} {room.commodity_listing.farmer.last_name}",
            current_highest_bid=room.current_highest_bid,
            current_highest_bidder=f"{room.current_highest_bidder.first_name} {room.current_highest_bidder.last_name}" if room.current_highest_bidder else None,
            total_bids=room.total_bids,
            active_participants=room.active_participants,
            is_active=room.is_active,
            created_at=room.created_at
        )
        room_responses.append(room_response)
    
    return AuctionRoomListResponse(
        success=True,
        message="Auction rooms retrieved successfully",
        data=room_responses
    )


@router.get("/auction-rooms/{commodity_id}", response_model=AuctionRoomResponseSchema)
async def get_auction_room(
    commodity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific auction room details"""
    
    room = await bid_manager.get_auction_room(db, commodity_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auction room not found")
    
    room_response = AuctionRoomResponse(
        commodity_listing_id=room.commodity_listing_id,
        commodity_title=room.commodity_listing.commodity_name,
        commodity_farmer=f"{room.commodity_listing.farmer.first_name} {room.commodity_listing.farmer.last_name}",
        current_highest_bid=room.current_highest_bid,
        current_highest_bidder=f"{room.current_highest_bidder.first_name} {room.current_highest_bidder.last_name}" if room.current_highest_bidder else None,
        total_bids=room.total_bids,
        active_participants=room.active_participants,
        is_active=room.is_active,
        created_at=room.created_at
    )
    
    return AuctionRoomResponseSchema(
        status="success",
        message="Auction room details retrieved",
        data=room_response
    )


@router.get("/stats/my-bidding", response_model=BidStatsResponseSchema)
async def get_my_bidding_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bidding statistics for current user"""
    
    # Get user's bids
    all_bids = await bid_manager.get_user_bids(db, current_user.id, limit=1000)
    
    if not all_bids:
        empty_stats = BidStatsResponse(
            total_bids=0,
            active_bids=0,
            accepted_bids=0,
            withdrawn_bids=0,
            average_bid_amount=None,
            highest_bid_amount=None,
            most_active_commodity=None
        )
        return BidStatsResponseSchema(
            status="success",
            message="No bidding activity found",
            data=empty_stats
        )
    
    # Calculate statistics        
    total_bids = len(all_bids)
    active_bids = len([b for b in all_bids if b.status == BidStatus.ACTIVE])
    accepted_bids = len([b for b in all_bids if b.status == BidStatus.ACCEPTED])
    withdrawn_bids = len([b for b in all_bids if b.status == BidStatus.WITHDRAWN])
    
    amounts = [float(bid.amount) for bid in all_bids]
    average_bid_amount = sum(amounts) / len(amounts)
    highest_bid_amount = max(amounts)
    
    # Find most active commodity
    commodity_counts = {}
    for bid in all_bids:
        commodity_id = bid.commodity_listing_id
        if commodity_id in commodity_counts:
            commodity_counts[commodity_id] += 1
        else:
            commodity_counts[commodity_id] = 1
    
    most_active_commodity_id = max(commodity_counts, key=commodity_counts.get) if commodity_counts else None
    most_active_commodity = None
    
    if most_active_commodity_id:
        # Find the commodity name
        for bid in all_bids:
            if bid.commodity_listing_id == most_active_commodity_id:
                most_active_commodity = bid.commodity_listing.commodity_name
                break
    
    stats = BidStatsResponse(
        total_bids=total_bids,
        active_bids=active_bids,
        accepted_bids=accepted_bids,
        withdrawn_bids=withdrawn_bids,
        average_bid_amount=average_bid_amount,
        highest_bid_amount=highest_bid_amount,
        most_active_commodity=most_active_commodity
    )
    
    return BidStatsResponseSchema(
        status="success",
        message="Bidding statistics retrieved",
        data=stats
    )
