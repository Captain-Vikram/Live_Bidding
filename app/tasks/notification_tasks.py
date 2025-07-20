"""
Notification Tasks
==================

Celery tasks for managing notifications and cleanup
"""

from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.db.managers.price_tracking import onsite_notification_manager, notification_log_manager
from app.core.config import settings
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.notification_tasks.cleanup_old_notifications")
def cleanup_old_notifications(self):
    """
    Clean up old read notifications and expired notifications
    """
    logger.info("Starting notification cleanup...")
    
    try:
        return asyncio.run(_cleanup_notifications_async())
    except Exception as e:
        logger.error(f"Error in notification cleanup task: {str(e)}")
        raise

async def _cleanup_notifications_async():
    """Async function to clean up old notifications"""
    
    async with SessionLocal() as db:
        cleanup_results = {}
        
        # Clean up old read on-site notifications
        read_cleanup_count = await onsite_notification_manager.cleanup_old_notifications(
            db=db, 
            days=settings.ONSITE_NOTIFICATION_RETENTION_DAYS
        )
        cleanup_results['old_read_notifications'] = read_cleanup_count
        
        # Clean up expired notifications
        expired_cleanup_count = await _cleanup_expired_notifications(db)
        cleanup_results['expired_notifications'] = expired_cleanup_count
        
        # Clean up old notification logs (keep for audit purposes, but not forever)
        # log_cleanup_count = await notification_log_manager.cleanup_old_logs(db, days=365)
        # cleanup_results['old_notification_logs'] = log_cleanup_count
        
        total_cleaned = sum(cleanup_results.values())
        
        logger.info(f"Notification cleanup completed: {total_cleaned} records cleaned")
        logger.info(f"Cleanup breakdown: {cleanup_results}")
        
        return {
            'status': 'SUCCESS',
            'total_cleaned': total_cleaned,
            'breakdown': cleanup_results,
            'timestamp': datetime.now().isoformat()
        }

async def _cleanup_expired_notifications(db) -> int:
    """Clean up notifications that have passed their expiry date"""
    
    from sqlalchemy import select, delete
    from app.db.models.price_tracking import OnSiteNotification
    
    # Delete expired notifications
    stmt = delete(OnSiteNotification).where(
        OnSiteNotification.expires_at < datetime.utcnow()
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount

@celery_app.task(bind=True, name="app.tasks.notification_tasks.send_notification_batch")
def send_notification_batch(self, notification_batch):
    """
    Send a batch of notifications (useful for bulk operations)
    """
    logger.info(f"Processing notification batch of {len(notification_batch)} notifications...")
    
    try:
        return asyncio.run(_send_batch_async(notification_batch))
    except Exception as e:
        logger.error(f"Error in batch notification task: {str(e)}")
        raise

async def _send_batch_async(notification_batch):
    """Process a batch of notifications"""
    
    async with SessionLocal() as db:
        successful_sends = 0
        failed_sends = 0
        
        for notification_data in notification_batch:
            try:
                # Create on-site notification
                await onsite_notification_manager.create_notification(
                    db=db,
                    user_id=notification_data['user_id'],
                    notification_data={
                        'title': notification_data['title'],
                        'message': notification_data['message'],
                        'notification_type': notification_data.get('type', 'GENERAL'),
                        'is_urgent': notification_data.get('is_urgent', False),
                        'metadata': notification_data.get('metadata'),
                        'action_url': notification_data.get('action_url')
                    }
                )
                
                successful_sends += 1
                
            except Exception as e:
                logger.error(f"Error sending notification to user {notification_data['user_id']}: {str(e)}")
                failed_sends += 1
        
        logger.info(f"Batch notification completed: {successful_sends} successful, {failed_sends} failed")
        
        return {
            'status': 'SUCCESS',
            'successful_sends': successful_sends,
            'failed_sends': failed_sends,
            'total_processed': len(notification_batch),
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name="app.tasks.notification_tasks.send_daily_summary")
def send_daily_summary():
    """
    Send daily summary notifications to users about their alerts and price changes
    """
    logger.info("Starting daily summary notification generation...")
    
    try:
        return asyncio.run(_send_daily_summary_async())
    except Exception as e:
        logger.error(f"Error in daily summary task: {str(e)}")
        raise

async def _send_daily_summary_async():
    """Generate and send daily summary notifications"""
    
    async with SessionLocal() as db:
        from app.db.managers.price_tracking import alert_subscription_manager
        from sqlalchemy import select, func
        from app.db.models.accounts import User
        
        summaries_sent = 0
        
        # Get users with active alert subscriptions
        stmt = select(User.id, User.email, User.full_name, func.count().label('alert_count')).join(
            User.alert_subscriptions
        ).where(
            User.alert_subscriptions.any(is_active=True)
        ).group_by(User.id, User.email, User.full_name)
        
        result = await db.execute(stmt)
        users_with_alerts = result.fetchall()
        
        for user_id, email, full_name, alert_count in users_with_alerts:
            try:
                # Get user's subscription summary
                user_subscriptions = await alert_subscription_manager.get_user_subscriptions(db, user_id)
                
                # Prepare summary data
                summary_data = {
                    'user_name': full_name,
                    'active_alerts': len(user_subscriptions),
                    'commodities_watched': list(set([sub.commodity.commodity_name for sub in user_subscriptions])),
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Create summary notification
                await onsite_notification_manager.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_data={
                        'title': 'Daily Market Summary',
                        'message': f"You have {alert_count} active price alerts watching {len(summary_data['commodities_watched'])} commodities.",
                        'notification_type': 'DAILY_SUMMARY',
                        'is_urgent': False,
                        'metadata': str(summary_data),  # JSON string
                        'action_url': '/alerts'
                    }
                )
                
                summaries_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending summary to user {user_id}: {str(e)}")
        
        logger.info(f"Daily summary completed: {summaries_sent} summaries sent")
        
        return {
            'status': 'SUCCESS',
            'summaries_sent': summaries_sent,
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name="app.tasks.notification_tasks.notify_price_milestone")
def notify_price_milestone(commodity_id, milestone_type, price_data):
    """
    Send notifications when a commodity reaches a price milestone
    (e.g., all-time high, 52-week low, etc.)
    """
    logger.info(f"Processing price milestone notification for commodity {commodity_id}")
    
    try:
        return asyncio.run(_notify_milestone_async(commodity_id, milestone_type, price_data))
    except Exception as e:
        logger.error(f"Error in milestone notification task: {str(e)}")
        raise

async def _notify_milestone_async(commodity_id, milestone_type, price_data):
    """Send milestone notifications to interested users"""
    
    async with SessionLocal() as db:
        from app.db.managers.price_tracking import alert_subscription_manager
        from app.db.models.listings import CommodityListing
        from sqlalchemy import select
        
        # Get commodity details
        stmt = select(CommodityListing).where(CommodityListing.id == commodity_id)
        result = await db.execute(stmt)
        commodity = result.scalar_one_or_none()
        
        if not commodity:
            return {'status': 'ERROR', 'message': 'Commodity not found'}
        
        # Get users watching this commodity
        subscriptions = await alert_subscription_manager.get_active_subscriptions_for_commodity(
            db, commodity_id
        )
        
        notifications_sent = 0
        
        milestone_messages = {
            'all_time_high': f"🚀 {commodity.commodity_name} reached an all-time high of ₹{price_data['price']}/kg!",
            'all_time_low': f"📉 {commodity.commodity_name} dropped to an all-time low of ₹{price_data['price']}/kg!",
            '52_week_high': f"📈 {commodity.commodity_name} hit a 52-week high of ₹{price_data['price']}/kg!",
            '52_week_low': f"📉 {commodity.commodity_name} reached a 52-week low of ₹{price_data['price']}/kg!",
            'significant_change': f"⚡ {commodity.commodity_name} price changed significantly: ₹{price_data['price']}/kg ({price_data['change_pct']:+.1f}%)"
        }
        
        title = f"Price Milestone: {commodity.commodity_name}"
        message = milestone_messages.get(milestone_type, f"Price milestone reached for {commodity.commodity_name}")
        
        # Send notifications to all watching users
        for subscription in subscriptions:
            try:
                await onsite_notification_manager.create_notification(
                    db=db,
                    user_id=subscription.user_id,
                    notification_data={
                        'title': title,
                        'message': message,
                        'notification_type': 'PRICE_MILESTONE',
                        'is_urgent': True,
                        'metadata': str(price_data),
                        'action_url': f'/commodities/{commodity_id}'
                    }
                )
                
                notifications_sent += 1
                
            except Exception as e:
                logger.error(f"Error sending milestone notification to user {subscription.user_id}: {str(e)}")
        
        logger.info(f"Milestone notifications sent: {notifications_sent} users notified")
        
        return {
            'status': 'SUCCESS',
            'milestone_type': milestone_type,
            'commodity_name': commodity.commodity_name,
            'notifications_sent': notifications_sent,
            'timestamp': datetime.now().isoformat()
        }
