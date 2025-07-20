"""
Price History Manager
====================

Business logic for price tracking and historical data management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from uuid import UUID

from app.db.managers.base import BaseManager
from app.db.models.price_tracking import PriceHistory, AlertSubscription, PriceAlert, AlertDirection
from app.db.models.listings import CommodityListing


class PriceHistoryManager(BaseManager[PriceHistory]):
    """Manager for price history operations"""
    
    async def add_price_data(
        self, 
        db: AsyncSession,
        commodity_id: UUID,
        date: date,
        avg_price: float,
        high_price: float,
        low_price: float,
        volume_kg: float = 0.0,
        market_name: Optional[str] = None,
        source: str = "manual"
    ) -> PriceHistory:
        """Add or update price data for a commodity on a specific date"""
        
        # Check if price data already exists for this date
        stmt = select(PriceHistory).where(
            and_(
                PriceHistory.commodity_id == commodity_id,
                PriceHistory.date == date
            )
        )
        existing = await db.execute(stmt)
        price_record = existing.scalar_one_or_none()
        
        if price_record:
            # Update existing record
            price_record.avg_price = avg_price
            price_record.high_price = high_price
            price_record.low_price = low_price
            price_record.volume_kg = volume_kg
            price_record.market_name = market_name
            price_record.source = source
        else:
            # Create new record
            price_record = PriceHistory(
                commodity_id=commodity_id,
                date=date,
                avg_price=avg_price,
                high_price=high_price,
                low_price=low_price,
                volume_kg=volume_kg,
                market_name=market_name,
                source=source
            )
            db.add(price_record)
        
        await db.commit()
        await db.refresh(price_record)
        return price_record
    
    async def get_price_history(
        self,
        db: AsyncSession,
        commodity_id: UUID,
        days: int = 30,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PriceHistory]:
        """Get price history for a commodity"""
        
        if not start_date and not end_date:
            # Default to last N days
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        
        stmt = select(PriceHistory).where(
            and_(
                PriceHistory.commodity_id == commodity_id,
                PriceHistory.date >= start_date,
                PriceHistory.date <= end_date
            )
        ).order_by(PriceHistory.date.desc())
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_latest_price(self, db: AsyncSession, commodity_id: UUID) -> Optional[PriceHistory]:
        """Get the most recent price data for a commodity"""
        
        stmt = select(PriceHistory).where(
            PriceHistory.commodity_id == commodity_id
        ).order_by(desc(PriceHistory.date)).limit(1)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_price_statistics(
        self,
        db: AsyncSession,
        commodity_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get price statistics for a commodity over specified period"""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        stmt = select(
            func.avg(PriceHistory.avg_price).label('avg_price'),
            func.min(PriceHistory.low_price).label('min_price'),
            func.max(PriceHistory.high_price).label('max_price'),
            func.sum(PriceHistory.volume_kg).label('total_volume'),
            func.count(PriceHistory.id).label('data_points')
        ).where(
            and_(
                PriceHistory.commodity_id == commodity_id,
                PriceHistory.date >= start_date,
                PriceHistory.date <= end_date
            )
        )
        
        result = await db.execute(stmt)
        stats = result.first()
        
        if not stats:
            return {}
        
        # Get current price for comparison
        latest = await self.get_latest_price(db, commodity_id)
        current_price = latest.avg_price if latest else None
        
        # Calculate price change
        price_change = None
        price_change_pct = None
        
        if current_price and stats.avg_price:
            price_change = current_price - stats.avg_price
            price_change_pct = (price_change / stats.avg_price) * 100
        
        return {
            'period_days': days,
            'current_price': current_price,
            'avg_price': float(stats.avg_price) if stats.avg_price else None,
            'min_price': float(stats.min_price) if stats.min_price else None,
            'max_price': float(stats.max_price) if stats.max_price else None,
            'total_volume': float(stats.total_volume) if stats.total_volume else 0,
            'data_points': stats.data_points,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'last_updated': latest.date if latest else None
        }
    
    async def get_trending_commodities(self, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        """Get commodities with significant price changes in the last 7 days"""
        
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Get commodities with recent price data
        stmt = select(PriceHistory.commodity_id).where(
            PriceHistory.date >= start_date
        ).distinct()
        
        result = await db.execute(stmt)
        commodity_ids = [row[0] for row in result.fetchall()]
        
        trending = []
        for commodity_id in commodity_ids:
            stats = await self.get_price_statistics(db, commodity_id, days=7)
            if stats.get('price_change_pct') is not None:
                # Get commodity details
                commodity_stmt = select(CommodityListing).where(CommodityListing.id == commodity_id)
                commodity_result = await db.execute(commodity_stmt)
                commodity = commodity_result.scalar_one_or_none()
                
                if commodity:
                    trending.append({
                        'commodity_id': str(commodity_id),
                        'commodity_name': commodity.commodity_name,
                        'current_price': stats['current_price'],
                        'price_change_pct': stats['price_change_pct'],
                        'avg_price_7d': stats['avg_price']
                    })
        
        # Sort by absolute price change percentage
        trending.sort(key=lambda x: abs(x['price_change_pct']), reverse=True)
        return trending[:limit]


class AlertSubscriptionManager(BaseManager[AlertSubscription]):
    """Manager for alert subscription operations"""
    
    async def create_subscription(
        self,
        db: AsyncSession,
        user_id: UUID,
        commodity_id: UUID,
        threshold_price: Optional[float] = None,
        threshold_pct: Optional[float] = None,
        direction: AlertDirection = AlertDirection.BUY,
        notify_email: bool = True,
        notify_sms: bool = False,
        notify_push: bool = True
    ) -> AlertSubscription:
        """Create a new alert subscription"""
        
        if not threshold_price and not threshold_pct:
            raise ValueError("Either threshold_price or threshold_pct must be provided")
        
        subscription = AlertSubscription(
            user_id=user_id,
            commodity_id=commodity_id,
            threshold_price=threshold_price,
            threshold_pct=threshold_pct,
            direction=direction,
            notify_email=notify_email,
            notify_sms=notify_sms,
            notify_push=notify_push
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription
    
    async def get_user_subscriptions(
        self,
        db: AsyncSession,
        user_id: UUID,
        active_only: bool = True
    ) -> List[AlertSubscription]:
        """Get all alert subscriptions for a user"""
        
        conditions = [AlertSubscription.user_id == user_id]
        if active_only:
            conditions.append(AlertSubscription.is_active == True)
        
        stmt = select(AlertSubscription).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_active_subscriptions_for_commodity(
        self,
        db: AsyncSession,
        commodity_id: UUID
    ) -> List[AlertSubscription]:
        """Get all active subscriptions for a commodity"""
        
        stmt = select(AlertSubscription).where(
            and_(
                AlertSubscription.commodity_id == commodity_id,
                AlertSubscription.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def deactivate_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        user_id: UUID
    ) -> bool:
        """Deactivate an alert subscription"""
        
        stmt = select(AlertSubscription).where(
            and_(
                AlertSubscription.id == subscription_id,
                AlertSubscription.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.is_active = False
            await db.commit()
            return True
        return False
    
    async def check_price_alerts(
        self,
        db: AsyncSession,
        commodity_id: UUID,
        current_price: float
    ) -> List[AlertSubscription]:
        """Check which subscriptions should be triggered by current price"""
        
        subscriptions = await self.get_active_subscriptions_for_commodity(db, commodity_id)
        triggered = []
        
        for subscription in subscriptions:
            should_trigger = False
            
            if subscription.threshold_price:
                # Direct price threshold
                if subscription.direction == AlertDirection.BUY and current_price <= subscription.threshold_price:
                    should_trigger = True
                elif subscription.direction == AlertDirection.SELL and current_price >= subscription.threshold_price:
                    should_trigger = True
            
            if subscription.threshold_pct:
                # Percentage change threshold (requires recent price history)
                # This would need to be implemented with historical comparison
                pass
            
            if should_trigger:
                triggered.append(subscription)
        
        return triggered


# Global manager instances
price_history_manager = PriceHistoryManager(PriceHistory)
alert_subscription_manager = AlertSubscriptionManager(AlertSubscription)

# NEW ENHANCED MANAGERS FOR PHASE 5

from app.db.models.price_tracking import OnSiteNotification, PriceNotificationLog

class OnSiteNotificationManager(BaseManager[OnSiteNotification]):
    """Manager for on-site notifications"""
    
    async def create_notification(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        notification_data: Dict[str, Any]
    ) -> OnSiteNotification:
        """Create a new on-site notification"""
        # Set expiry if not provided (default 3 days)
        if 'expires_at' not in notification_data:
            notification_data['expires_at'] = datetime.utcnow() + timedelta(days=3)
        
        notification = OnSiteNotification(
            user_id=user_id,
            **notification_data
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification
    
    async def get_user_notifications(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        limit: int = 50,
        unread_only: bool = False
    ) -> List[OnSiteNotification]:
        """Get notifications for a user"""
        conditions = [OnSiteNotification.user_id == user_id]
        
        if unread_only:
            conditions.append(OnSiteNotification.is_read == False)
        
        # Exclude expired notifications
        conditions.append(
            or_(
                OnSiteNotification.expires_at.is_(None),
                OnSiteNotification.expires_at > datetime.utcnow()
            )
        )
        
        stmt = select(OnSiteNotification).where(
            and_(*conditions)
        ).order_by(
            desc(OnSiteNotification.is_urgent),
            desc(OnSiteNotification.created_at)
        ).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def mark_as_read(self, db: AsyncSession, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read"""
        stmt = select(OnSiteNotification).where(
            and_(
                OnSiteNotification.id == notification_id,
                OnSiteNotification.user_id == user_id
            )
        )
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await db.commit()
            return True
        return False
    
    async def get_unread_count(self, db: AsyncSession, user_id: UUID) -> int:
        """Get count of unread notifications for a user"""
        stmt = select(func.count()).select_from(OnSiteNotification).where(
            and_(
                OnSiteNotification.user_id == user_id,
                OnSiteNotification.is_read == False,
                or_(
                    OnSiteNotification.expires_at.is_(None),
                    OnSiteNotification.expires_at > datetime.utcnow()
                )
            )
        )
        
        result = await db.execute(stmt)
        return result.scalar() or 0

class NotificationLogManager(BaseManager[PriceNotificationLog]):
    """Manager for notification logs"""
    
    async def log_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        channel: str,
        title: str,
        content: str,
        alert_subscription_id: Optional[UUID] = None
    ) -> PriceNotificationLog:
        """Log a notification delivery attempt"""
        log_entry = PriceNotificationLog(
            user_id=user_id,
            alert_subscription_id=alert_subscription_id,
            channel=channel,
            title=title,
            content=content,
            status="PENDING"
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry

# Enhanced manager instances
onsite_notification_manager = OnSiteNotificationManager(OnSiteNotification)
notification_log_manager = NotificationLogManager(PriceNotificationLog)
