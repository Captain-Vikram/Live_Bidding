from typing import List, Dict, Set
from uuid import UUID
import json
import asyncio
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import redis_manager
from app.db.managers.bidding import bid_manager
from app.db.managers.commodities import commodity_listing_manager
from app.api.utils.auth import get_current_user_ws
from app.db.models.accounts import User

logger = logging.getLogger(__name__)

router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections for auction rooms"""
    
    def __init__(self):
        # Store active connections by commodity_id -> {user_id: websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Track user sessions
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of commodity_ids
    
    async def connect(self, websocket: WebSocket, commodity_id: str, user_id: str):
        """Connect user to auction room"""
        await websocket.accept()
        
        # Initialize commodity room if not exists
        if commodity_id not in self.active_connections:
            self.active_connections[commodity_id] = {}
        
        # Add connection
        self.active_connections[commodity_id][user_id] = websocket
        
        # Track user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(commodity_id)
        
        # Add to Redis participants
        await redis_manager.add_participant(commodity_id, user_id)
        
        logger.info(f"User {user_id} connected to auction room {commodity_id}")
        
        # Notify other participants
        await self.broadcast_user_activity(commodity_id, user_id, "joined")
        
        return websocket
    
    async def disconnect(self, commodity_id: str, user_id: str):
        """Disconnect user from auction room"""
        try:
            # Remove from active connections
            if commodity_id in self.active_connections:
                self.active_connections[commodity_id].pop(user_id, None)
                
                # Clean up empty rooms
                if not self.active_connections[commodity_id]:
                    del self.active_connections[commodity_id]
            
            # Remove from user sessions
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(commodity_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Remove from Redis participants
            await redis_manager.remove_participant(commodity_id, user_id)
            
            logger.info(f"User {user_id} disconnected from auction room {commodity_id}")
            
            # Notify other participants
            await self.broadcast_user_activity(commodity_id, user_id, "left")
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id} from room {commodity_id}: {e}")
    
    async def send_personal_message(self, message: dict, commodity_id: str, user_id: str):
        """Send message to specific user"""
        try:
            if commodity_id in self.active_connections and user_id in self.active_connections[commodity_id]:
                websocket = self.active_connections[commodity_id][user_id]
                await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending personal message to {user_id}: {e}")
            # Remove broken connection
            await self.disconnect(commodity_id, user_id)
    
    async def broadcast_to_room(self, message: dict, commodity_id: str, exclude_user: str = None):
        """Broadcast message to all users in auction room"""
        if commodity_id not in self.active_connections:
            return
        
        disconnected_users = []
        
        for user_id, websocket in self.active_connections[commodity_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(commodity_id, user_id)
    
    async def broadcast_user_activity(self, commodity_id: str, user_id: str, action: str):
        """Broadcast user join/leave activity"""
        count = await redis_manager.get_participant_count(commodity_id)
        
        message = {
            "type": "user_activity",
            "data": {
                "user_id": user_id,
                "action": action,
                "participant_count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await self.broadcast_to_room(message, commodity_id, exclude_user=user_id)
    
    def get_room_connections(self, commodity_id: str) -> int:
        """Get number of active connections in room"""
        return len(self.active_connections.get(commodity_id, {}))
    
    def get_user_rooms(self, user_id: str) -> Set[str]:
        """Get all rooms user is connected to"""
        return self.user_sessions.get(user_id, set())


# Global WebSocket manager
ws_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_test_endpoint(websocket: WebSocket):
    """Basic WebSocket endpoint for testing connectivity"""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "WebSocket connection successful",
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "message": "WebSocket is working",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "message": f"Received: {data}",
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.websocket("/ws/auction/{commodity_id}")
async def websocket_auction_endpoint(
    websocket: WebSocket,
    commodity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for auction room"""
    user = None
    
    try:
        # Get current user from WebSocket
        user = await get_current_user_ws(websocket, db)
        commodity_id_str = str(commodity_id)
        user_id_str = str(user.id)
        
        # Verify commodity exists and is active
        commodity = await commodity_listing_manager.get_by_id(db, commodity_id)
        if not commodity or not commodity.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Commodity not found or inactive")
            return
        
        # Connect to auction room
        await ws_manager.connect(websocket, commodity_id_str, user_id_str)
        
        # Send welcome message with room info
        room_info = await bid_manager.get_auction_room(db, commodity_id)
        participant_count = await redis_manager.get_participant_count(commodity_id_str)
        
        welcome_message = {
            "type": "welcome",
            "data": {
                "commodity_id": commodity_id_str,
                "commodity_title": commodity.commodity_name,
                "current_highest_bid": float(room_info.current_highest_bid) if room_info and room_info.current_highest_bid else None,
                "participant_count": participant_count,
                "user_role": user.role.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await ws_manager.send_personal_message(welcome_message, commodity_id_str, user_id_str)
        
        # Send recent bids
        recent_bids = await bid_manager.get_bids_for_commodity(db, commodity_id, limit=10)
        if recent_bids:
            bids_message = {
                "type": "recent_bids",
                "data": {
                    "bids": [
                        {
                            "id": str(bid.id),
                            "bidder_name": bid.user.first_name,
                            "amount": float(bid.amount),
                            "timestamp": bid.bid_time.isoformat(),
                            "message": bid.message
                        }
                        for bid in recent_bids
                    ]
                }
            }
            await ws_manager.send_personal_message(bids_message, commodity_id_str, user_id_str)
        
        # Listen for Redis messages (new bids from other instances)
        async def redis_listener():
            channel = f"auction:{commodity_id_str}"
            async for message in redis_manager.listen(channel):
                await ws_manager.broadcast_to_room(message, commodity_id_str)
        
        # Start Redis listener in background
        redis_task = asyncio.create_task(redis_listener())
        
        # Handle WebSocket messages
        try:
            while True:
                # Wait for client messages
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping
                        pong_message = {
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await ws_manager.send_personal_message(pong_message, commodity_id_str, user_id_str)
                    
                    elif message_type == "get_participants":
                        # Send current participant count
                        count = await redis_manager.get_participant_count(commodity_id_str)
                        participants_message = {
                            "type": "participants_update",
                            "data": {
                                "count": count,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                        await ws_manager.send_personal_message(participants_message, commodity_id_str, user_id_str)
                    
                    elif message_type == "typing":
                        # Broadcast typing indicator
                        typing_message = {
                            "type": "user_typing",
                            "data": {
                                "user_name": user.first_name,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        }
                        await ws_manager.broadcast_to_room(typing_message, commodity_id_str, exclude_user=user_id_str)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from user {user_id_str}")
                    
        except WebSocketDisconnect:
            pass
        finally:
            # Cancel Redis listener
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.client_state.value == 1:  # Connected
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    
    finally:
        # Clean up connection
        if user:
            await ws_manager.disconnect(str(commodity_id), str(user.id))


@router.get("/auction-rooms/active")
async def get_active_auction_rooms(
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """Get list of active auction rooms"""
    try:
        rooms = await bid_manager.get_active_auction_rooms(db, limit)
        
        room_data = []
        for room in rooms:
            try:
                participant_count = await redis_manager.get_participant_count(str(room.commodity_listing_id))
            except Exception as e:
                logger.warning(f"Redis error for room {room.commodity_listing_id}: {e}")
                participant_count = 0  # Default to 0 if Redis fails
            
            room_data.append({
                "commodity_id": str(room.commodity_listing_id),
                "commodity_title": room.commodity_listing.commodity_name,
                "current_highest_bid": float(room.current_highest_bid) if room.current_highest_bid else None,
                "total_bids": room.total_bids,
                "active_participants": participant_count,
                "farmer_name": room.commodity_listing.farmer.first_name,
                "created_at": room.created_at.isoformat()
            })
        
        return {
            "success": True,
            "message": "Active auction rooms retrieved",
            "data": room_data
        }
    except Exception as e:
        logger.error(f"Error getting active auction rooms: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve auction rooms")


@router.get("/auction-rooms/{commodity_id}/stats")
async def get_auction_room_stats(
    commodity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get auction room statistics"""
    
    try:
        # Get auction room
        room = await bid_manager.get_auction_room(db, commodity_id)
        if not room:
            raise HTTPException(status_code=404, detail="Auction room not found")
        
        # Get participant data with error handling
        try:
            participant_count = await redis_manager.get_participant_count(str(commodity_id))
        except Exception as e:
            logger.warning(f"Redis error for stats {commodity_id}: {e}")
            participant_count = 0
            
        active_connections = ws_manager.get_room_connections(str(commodity_id))
        
        # Get recent bid activity
        recent_bids = await bid_manager.get_bids_for_commodity(db, commodity_id, limit=5)
        
        return {
            "success": True,
            "message": "Auction room stats retrieved",
            "data": {
                "commodity_id": str(commodity_id),
                "total_bids": room.total_bids,
                "current_highest_bid": float(room.current_highest_bid) if room.current_highest_bid else None,
                "participant_count": participant_count,
                "active_connections": active_connections,
                "is_active": room.is_active,
                "recent_bids": [
                    {
                        "amount": float(bid.amount),
                        "bidder_name": bid.user.first_name,
                        "timestamp": bid.bid_time.isoformat()
                    }
                    for bid in recent_bids
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting auction room stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve auction room stats")
