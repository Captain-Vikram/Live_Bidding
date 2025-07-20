import redis.asyncio as redis
import json
from typing import Any, Dict, Optional, List
import asyncio
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis manager for pub/sub messaging and caching"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.active_connections: Dict[str, List] = {}
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Disconnected from Redis")
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        if not self.redis_client:
            await self.connect()
        
        try:
            message_str = json.dumps(message, default=str)
            await self.redis_client.publish(channel, message_str)
            logger.debug(f"Published message to {channel}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to {channel}: {e}")
    
    async def subscribe(self, channel: str):
        """Subscribe to channel"""
        if not self.redis_client:
            await self.connect()
        
        if not self.pubsub:
            self.pubsub = self.redis_client.pubsub()
        
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")
    
    async def listen(self, channel: str):
        """Listen for messages on channel"""
        await self.subscribe(channel)
        
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message['data']}")
    
    async def set_cache(self, key: str, value: Any, expire: Optional[int] = None):
        """Set a value in Redis cache"""
        if not self.redis_client:
            await self.connect()
        
        try:
            value_str = json.dumps(value, default=str)
            await self.redis_client.set(key, value_str, ex=expire)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get value by key"""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def delete_cache(self, key: str):
        """Delete key"""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
    
    async def increment_counter(self, key: str, expire: Optional[int] = None) -> int:
        """Increment counter and return new value"""
        if not self.redis_client:
            await self.connect()
        
        try:
            count = await self.redis_client.incr(key)
            if expire and count == 1:  # Set expiration only on first increment
                await self.redis_client.expire(key, expire)
            return count
        except Exception as e:
            logger.error(f"Failed to increment counter {key}: {e}")
            return 0
    
    async def get_counter(self, key: str) -> int:
        """Get counter value"""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Failed to get counter {key}: {e}")
            return 0
    
    async def add_to_set(self, key: str, value: str):
        """Add value to set"""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.sadd(key, value)
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {e}")
    
    async def remove_from_set(self, key: str, value: str):
        """Remove value from set"""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.srem(key, value)
        except Exception as e:
            logger.error(f"Failed to remove from set {key}: {e}")
    
    async def get_set_members(self, key: str) -> List[str]:
        """Get all members of set"""
        if not self.redis_client:
            await self.connect()
        
        try:
            members = await self.redis_client.smembers(key)
            return list(members) if members else []
        except Exception as e:
            logger.error(f"Failed to get set members {key}: {e}")
            return []
    
    async def add_participant(self, commodity_id: str, user_id: str):
        """Add participant to auction room"""
        try:
            if not self.redis_client:
                await self.connect()
            
            key = f"auction_participants:{commodity_id}"
            await self.add_to_set(key, user_id)
            
            # Update participant count
            count_key = f"auction_count:{commodity_id}"
            count = await self.increment_counter(count_key, expire=3600)
            return count
        except Exception as e:
            logger.error(f"Failed to add participant {user_id} to {commodity_id}: {e}")
            return 1  # Return default count to prevent failures
    
    async def remove_participant(self, commodity_id: str, user_id: str):
        """Remove participant from auction room"""
        try:
            if not self.redis_client:
                await self.connect()
                
            key = f"auction_participants:{commodity_id}"
            await self.remove_from_set(key, user_id)
        except Exception as e:
            logger.error(f"Failed to remove participant {user_id} from {commodity_id}: {e}")
    
    async def get_participants(self, commodity_id: str) -> List[str]:
        """Get auction room participants"""
        try:
            if not self.redis_client:
                await self.connect()
                
            key = f"auction_participants:{commodity_id}"
            return await self.get_set_members(key)
        except Exception as e:
            logger.error(f"Failed to get participants for {commodity_id}: {e}")
            return []
    
    async def get_participant_count(self, commodity_id: str) -> int:
        """Get participant count"""
        try:
            if not self.redis_client:
                await self.connect()
                
            key = f"auction_count:{commodity_id}"
            return await self.get_counter(key)
        except Exception as e:
            logger.error(f"Failed to get participant count for {commodity_id}: {e}")
            return 0
    
    async def is_healthy(self) -> bool:
        """Check Redis health"""
        try:
            if not self.redis_client:
                await self.connect()
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis manager instance
redis_manager = RedisManager()
