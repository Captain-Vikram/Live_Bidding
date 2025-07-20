"""
Mobile and Notification Management
==================================

Database managers for mobile device registration, notifications, and user activity tracking
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timedelta

from app.db.managers.base import BaseManager
from app.db.models.mobile import (
    DeviceRegistration, NotificationPreference, NotificationLog, 
    UserActivity, UserLocation, DeviceType, NotificationChannel
)


class DeviceRegistrationManager(BaseManager[DeviceRegistration]):
    """Manager for mobile device registrations"""
    
    async def register_device(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        device_token: str, 
        device_type: DeviceType,
        device_info: Optional[Dict] = None,
        app_version: Optional[str] = None,
        os_version: Optional[str] = None
    ) -> DeviceRegistration:
        """Register or update a device for push notifications"""
        
        # Check if device already exists
        existing = await db.execute(
            select(self.model).where(
                and_(
                    self.model.device_token == device_token,
                    self.model.user_id == user_id
                )
            )
        )
        device = existing.scalar_one_or_none()
        
        if device:
            # Update existing device
            device.device_type = device_type
            device.device_info = device_info
            device.app_version = app_version
            device.os_version = os_version
            device.is_active = True
            device.last_active = datetime.utcnow()
        else:
            # Create new device registration
            device = self.model(
                user_id=user_id,
                device_token=device_token,
                device_type=device_type,
                device_info=device_info,
                app_version=app_version,
                os_version=os_version
            )
            db.add(device)
        
        await db.commit()
        await db.refresh(device)
        return device
    
    async def get_user_devices(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        active_only: bool = True
    ) -> List[DeviceRegistration]:
        """Get all devices for a user"""
        
        query = select(self.model).where(self.model.user_id == user_id)
        
        if active_only:
            query = query.where(self.model.is_active == True)
        
        result = await db.execute(query.order_by(desc(self.model.last_active)))
        return result.scalars().all()
    
    async def deactivate_device(
        self, 
        db: AsyncSession, 
        device_token: str, 
        user_id: UUID
    ) -> bool:
        """Deactivate a device registration"""
        
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.device_token == device_token,
                    self.model.user_id == user_id
                )
            )
        )
        device = result.scalar_one_or_none()
        
        if device:
            device.is_active = False
            await db.commit()
            return True
        
        return False
    
    async def cleanup_inactive_devices(self, db: AsyncSession, days: int = 30):
        """Remove devices that haven't been active for specified days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.last_active < cutoff_date,
                    self.model.is_active == False
                )
            )
        )
        
        devices_to_delete = result.scalars().all()
        for device in devices_to_delete:
            await db.delete(device)
        
        await db.commit()
        return len(devices_to_delete)


class NotificationPreferenceManager(BaseManager[NotificationPreference]):
    """Manager for user notification preferences"""
    
    async def get_or_create_preferences(
        self, 
        db: AsyncSession, 
        user_id: UUID
    ) -> NotificationPreference:
        """Get user preferences or create default ones"""
        
        result = await db.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            preferences = self.model(user_id=user_id)
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        
        return preferences
    
    async def update_preferences(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        **updates
    ) -> NotificationPreference:
        """Update user notification preferences"""
        
        preferences = await self.get_or_create_preferences(db, user_id)
        
        for field, value in updates.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)
        
        await db.commit()
        await db.refresh(preferences)
        return preferences
    
    async def check_notification_allowed(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        notification_type: str, 
        channel: NotificationChannel
    ) -> bool:
        """Check if a notification is allowed based on user preferences"""
        
        preferences = await self.get_or_create_preferences(db, user_id)
        
        # Check channel preferences
        channel_enabled = {
            NotificationChannel.EMAIL: preferences.email_enabled,
            NotificationChannel.SMS: preferences.sms_enabled,
            NotificationChannel.PUSH: preferences.push_enabled,
            NotificationChannel.IN_APP: preferences.in_app_enabled,
        }.get(channel, False)
        
        if not channel_enabled:
            return False
        
        # Check notification type preferences
        type_enabled = {
            "trade_updates": preferences.trade_updates,
            "market_reminders": preferences.market_reminders,
            "price_alerts": preferences.price_alerts,
            "listing_updates": preferences.listing_updates,
            "payment_notifications": preferences.payment_notifications,
            "marketing_notifications": preferences.marketing_notifications,
        }.get(notification_type, True)
        
        if not type_enabled:
            return False
        
        # Check quiet hours (simplified - would need timezone handling in production)
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            current_time = datetime.utcnow().strftime("%H:%M")
            if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                # Skip non-urgent notifications during quiet hours
                urgent_types = ["payment_notifications", "trade_updates"]
                if notification_type not in urgent_types:
                    return False
        
        return True


class NotificationLogManager(BaseManager[NotificationLog]):
    """Manager for notification logging and tracking"""
    
    async def log_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        notification_type: str,
        channel: NotificationChannel,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ) -> NotificationLog:
        """Log a notification attempt"""
        
        log_entry = self.model(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            title=title,
            message=message,
            data=data
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry
    
    async def update_delivery_status(
        self,
        db: AsyncSession,
        log_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Update notification delivery status"""
        
        result = await db.execute(
            select(self.model).where(self.model.id == log_id)
        )
        log_entry = result.scalar_one_or_none()
        
        if log_entry:
            log_entry.status = status
            if status == "sent":
                log_entry.sent_at = datetime.utcnow()
            elif status == "delivered":
                log_entry.delivered_at = datetime.utcnow()
            
            if error_message:
                log_entry.error_message = error_message
            
            await db.commit()
            return True
        
        return False
    
    async def mark_clicked(self, db: AsyncSession, log_id: UUID) -> bool:
        """Mark notification as clicked"""
        
        result = await db.execute(
            select(self.model).where(self.model.id == log_id)
        )
        log_entry = result.scalar_one_or_none()
        
        if log_entry:
            log_entry.clicked = True
            log_entry.clicked_at = datetime.utcnow()
            await db.commit()
            return True
        
        return False
    
    async def get_user_notification_history(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[NotificationLog]:
        """Get notification history for a user"""
        
        result = await db.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        return result.scalars().all()
    
    async def get_notification_analytics(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get notification analytics"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total notifications
        total_result = await db.execute(
            select(func.count(self.model.id))
            .where(self.model.created_at >= cutoff_date)
        )
        total_notifications = total_result.scalar()
        
        # Delivery rates by channel
        channel_stats = await db.execute(
            select(
                self.model.channel,
                func.count(self.model.id).label('total'),
                func.sum(func.case((self.model.status == 'delivered', 1), else_=0)).label('delivered')
            )
            .where(self.model.created_at >= cutoff_date)
            .group_by(self.model.channel)
        )
        
        # Click rates
        click_stats = await db.execute(
            select(
                func.count(self.model.id).label('total'),
                func.sum(func.case((self.model.clicked == True, 1), else_=0)).label('clicked')
            )
            .where(self.model.created_at >= cutoff_date)
        )
        
        return {
            "total_notifications": total_notifications,
            "channel_stats": [
                {
                    "channel": row.channel,
                    "total": row.total,
                    "delivered": row.delivered,
                    "delivery_rate": (row.delivered / row.total * 100) if row.total > 0 else 0
                }
                for row in channel_stats
            ],
            "overall_click_rate": (click_stats.scalar().clicked / click_stats.scalar().total * 100) if click_stats.scalar().total > 0 else 0
        }


class UserActivityManager(BaseManager[UserActivity]):
    """Manager for user activity tracking"""
    
    async def track_activity(
        self,
        db: AsyncSession,
        user_id: Optional[UUID],
        activity_type: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        data: Optional[Dict] = None,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserActivity:
        """Track user activity"""
        
        activity = self.model(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        db.add(activity)
        await db.commit()
        await db.refresh(activity)
        return activity
    
    async def get_user_activity_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Activity counts by type
        activity_counts = await db.execute(
            select(
                self.model.activity_type,
                func.count(self.model.id).label('count')
            )
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.created_at >= cutoff_date
                )
            )
            .group_by(self.model.activity_type)
        )
        
        # Most viewed resources
        resource_views = await db.execute(
            select(
                self.model.resource_type,
                self.model.resource_id,
                func.count(self.model.id).label('view_count')
            )
            .where(
                and_(
                    self.model.user_id == user_id,
                    self.model.activity_type == 'view',
                    self.model.created_at >= cutoff_date
                )
            )
            .group_by(self.model.resource_type, self.model.resource_id)
            .order_by(desc('view_count'))
            .limit(10)
        )
        
        return {
            "activity_counts": {row.activity_type: row.count for row in activity_counts},
            "top_viewed_resources": [
                {
                    "resource_type": row.resource_type,
                    "resource_id": str(row.resource_id),
                    "view_count": row.view_count
                }
                for row in resource_views
            ]
        }


class UserLocationManager(BaseManager[UserLocation]):
    """Manager for user location data"""
    
    async def save_location(
        self,
        db: AsyncSession,
        user_id: UUID,
        latitude: str,
        longitude: str,
        accuracy: Optional[int] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        location_type: Optional[str] = None,
        is_primary: bool = False
    ) -> UserLocation:
        """Save user location"""
        
        # If setting as primary, remove primary flag from other locations
        if is_primary:
            await db.execute(
                select(self.model)
                .where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.is_primary == True
                    )
                )
            )
            existing_primary = await db.execute(
                select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.is_primary == True
                    )
                )
            )
            for location in existing_primary.scalars():
                location.is_primary = False
        
        location = self.model(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            location_type=location_type,
            is_primary=is_primary
        )
        
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location
    
    async def get_user_locations(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> List[UserLocation]:
        """Get all user locations"""
        
        result = await db.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.is_primary), desc(self.model.created_at))
        )
        
        return result.scalars().all()
    
    async def get_primary_location(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[UserLocation]:
        """Get user's primary location"""
        
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.is_primary == True
                )
            )
        )
        
        return result.scalar_one_or_none()


# Create manager instances
device_manager = DeviceRegistrationManager(DeviceRegistration)
notification_preference_manager = NotificationPreferenceManager(NotificationPreference)
notification_log_manager = NotificationLogManager(NotificationLog)
user_activity_manager = UserActivityManager(UserActivity)
user_location_manager = UserLocationManager(UserLocation)
