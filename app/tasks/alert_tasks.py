"""
Alert Processing Tasks
=====================

Celery tasks for checking price alerts and sending notifications
"""

from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.db.managers.price_tracking import (
    alert_subscription_manager, 
    price_history_manager,
    onsite_notification_manager,
    notification_log_manager
)
from app.db.models.price_tracking import AlertDirection
from app.api.utils.emails import send_email
from app.core.config import settings
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import json

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.alert_tasks.check_price_alerts")
def check_price_alerts(self):
    """
    Check all active price alerts and trigger notifications
    """
    logger.info("Starting price alert check...")
    
    try:
        return asyncio.run(_check_alerts_async())
    except Exception as e:
        logger.error(f"Error in alert check task: {str(e)}")
        raise

async def _check_alerts_async():
    """Async function to check and process alerts"""
    
    async with SessionLocal() as db:
        alerts_triggered = 0
        notifications_sent = 0
        
        # Get all active alert subscriptions
        subscriptions = await alert_subscription_manager.get_all_active_subscriptions(db)
        
        logger.info(f"Checking {len(subscriptions)} active alert subscriptions")
        
        for subscription in subscriptions:
            try:
                # Skip if already hit daily limit
                if subscription.trigger_count_today >= subscription.max_triggers_per_day:
                    continue
                
                # Get latest price for this commodity
                latest_price = await price_history_manager.get_latest_price(
                    db=db, 
                    commodity_id=subscription.commodity_id
                )
                
                if not latest_price:
                    continue
                
                # Check if alert should be triggered
                should_trigger = await _should_trigger_alert(subscription, latest_price, db)
                
                if should_trigger:
                    # Trigger the alert
                    await _trigger_alert(db, subscription, latest_price)
                    alerts_triggered += 1
                    
                    # Send notifications
                    sent_count = await _send_alert_notifications(db, subscription, latest_price)
                    notifications_sent += sent_count
                    
                    logger.info(f"Alert triggered for {subscription.commodity.commodity_name} - Price: ₹{latest_price.avg_price}")
                
            except Exception as e:
                logger.error(f"Error processing alert {subscription.id}: {str(e)}")
        
        logger.info(f"Alert check completed: {alerts_triggered} alerts triggered, {notifications_sent} notifications sent")
        
        return {
            'status': 'SUCCESS',
            'alerts_triggered': alerts_triggered,
            'notifications_sent': notifications_sent,
            'subscriptions_checked': len(subscriptions),
            'timestamp': datetime.now().isoformat()
        }

async def _should_trigger_alert(subscription, latest_price, db) -> bool:
    """Check if an alert should be triggered based on subscription criteria"""
    
    current_price = float(latest_price.avg_price)
    threshold_price = float(subscription.threshold_price)
    
    # Check price threshold
    if subscription.direction == AlertDirection.BUY:
        # Alert when price drops to or below threshold (good for buying)
        if current_price <= threshold_price:
            return True
    elif subscription.direction == AlertDirection.SELL:
        # Alert when price rises to or above threshold (good for selling)
        if current_price >= threshold_price:
            return True
    
    # Check percentage change threshold if set
    if subscription.threshold_pct:
        # Get price from yesterday for comparison
        yesterday = date.today() - timedelta(days=1)
        yesterday_price = await price_history_manager.get_price_for_date(
            db=db,
            commodity_id=subscription.commodity_id,
            date=yesterday
        )
        
        if yesterday_price:
            price_change_pct = ((current_price - float(yesterday_price.avg_price)) / float(yesterday_price.avg_price)) * 100
            
            if abs(price_change_pct) >= float(subscription.threshold_pct):
                return True
    
    return False

async def _trigger_alert(db, subscription, latest_price):
    """Mark alert as triggered and update counters"""
    
    # Update subscription trigger info
    subscription.last_triggered = datetime.utcnow()
    subscription.trigger_count_today += 1
    
    # Create price alert record (if PriceAlert model is used)
    # This could be implemented if you want to keep a log of all triggered alerts
    
    await db.commit()

async def _send_alert_notifications(db, subscription, latest_price) -> int:
    """Send notifications through enabled channels"""
    
    notifications_sent = 0
    current_price = float(latest_price.avg_price)
    threshold_price = float(subscription.threshold_price)
    
    # Prepare notification content
    notification_data = {
        'commodity_name': subscription.commodity.commodity_name,
        'current_price': current_price,
        'threshold_price': threshold_price,
        'direction': subscription.direction.value,
        'market_name': latest_price.market_name,
        'date': latest_price.date.isoformat()
    }
    
    title = f"Price Alert: {subscription.commodity.commodity_name}"
    
    if subscription.direction == AlertDirection.BUY:
        message = f"Great time to BUY! {subscription.commodity.commodity_name} price dropped to ₹{current_price}/kg (Target: ₹{threshold_price}/kg)"
    else:
        message = f"Great time to SELL! {subscription.commodity.commodity_name} price reached ₹{current_price}/kg (Target: ₹{threshold_price}/kg)"
    
    # 1. On-site notification (if enabled)
    if subscription.notify_onsite:
        try:
            await onsite_notification_manager.create_notification(
                db=db,
                user_id=subscription.user_id,
                notification_data={
                    'title': title,
                    'message': message,
                    'notification_type': 'PRICE_ALERT',
                    'is_urgent': True,
                    'metadata': json.dumps(notification_data),
                    'action_url': f"/commodities/{subscription.commodity.id}"
                }
            )
            notifications_sent += 1
            
            # Log the notification
            await notification_log_manager.log_notification(
                db=db,
                user_id=subscription.user_id,
                channel="ONSITE",
                title=title,
                content=message,
                alert_subscription_id=subscription.id
            )
            
        except Exception as e:
            logger.error(f"Error sending on-site notification: {str(e)}")
    
    # 2. Email notification (if enabled)
    if subscription.notify_email:
        try:
            email_content = _prepare_email_content(subscription, notification_data)
            
            # This would integrate with your existing email system
            # await send_email(
            #     background_tasks=None,
            #     db=db,
            #     user=subscription.user,
            #     template_type="price_alert",
            #     content=email_content
            # )
            
            notifications_sent += 1
            
            # Log the notification
            await notification_log_manager.log_notification(
                db=db,
                user_id=subscription.user_id,
                channel="EMAIL",
                title=title,
                content=message,
                alert_subscription_id=subscription.id
            )
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
    
    # 3. SMS notification (if enabled)
    if subscription.notify_sms and subscription.user.phone_number:
        try:
            # SMS integration would go here
            # await send_sms(subscription.user.phone_number, message)
            
            notifications_sent += 1
            
            # Log the notification
            await notification_log_manager.log_notification(
                db=db,
                user_id=subscription.user_id,
                channel="SMS",
                title=title,
                content=message,
                alert_subscription_id=subscription.id
            )
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
    
    # 4. Push notification (if enabled)
    if subscription.notify_push:
        try:
            # Push notification integration would go here
            # await send_push_notification(subscription.user_id, title, message)
            
            notifications_sent += 1
            
            # Log the notification
            await notification_log_manager.log_notification(
                db=db,
                user_id=subscription.user_id,
                channel="PUSH",
                title=title,
                content=message,
                alert_subscription_id=subscription.id
            )
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
    
    return notifications_sent

def _prepare_email_content(subscription, notification_data) -> Dict[str, Any]:
    """Prepare email content for price alert"""
    
    return {
        'subject': f"Price Alert: {notification_data['commodity_name']}",
        'template': 'price_alert',
        'context': {
            'user_name': subscription.user.full_name,
            'commodity_name': notification_data['commodity_name'],
            'current_price': notification_data['current_price'],
            'threshold_price': notification_data['threshold_price'],
            'direction': notification_data['direction'],
            'market_name': notification_data['market_name'],
            'alert_date': notification_data['date'],
            'recommendation': 'BUY' if subscription.direction == AlertDirection.BUY else 'SELL'
        }
    }

@celery_app.task(name="app.tasks.alert_tasks.reset_daily_alert_counts")
def reset_daily_alert_counts():
    """Reset daily alert trigger counts (run at midnight)"""
    logger.info("Resetting daily alert trigger counts...")
    
    try:
        return asyncio.run(_reset_counts_async())
    except Exception as e:
        logger.error(f"Error in reset counts task: {str(e)}")
        raise

async def _reset_counts_async():
    """Reset daily trigger counts for all subscriptions"""
    
    async with SessionLocal() as db:
        reset_count = await alert_subscription_manager.reset_daily_trigger_counts(db)
        
        logger.info(f"Reset trigger counts for {reset_count} subscriptions")
        
        return {
            'status': 'SUCCESS',
            'subscriptions_reset': reset_count,
            'timestamp': datetime.now().isoformat()
        }

@celery_app.task(name="app.tasks.alert_tasks.cleanup_old_alerts")
def cleanup_old_alerts():
    """Clean up old alert logs and notifications"""
    logger.info("Starting alert cleanup...")
    
    try:
        return asyncio.run(_cleanup_alerts_async())
    except Exception as e:
        logger.error(f"Error in alert cleanup task: {str(e)}")
        raise

async def _cleanup_alerts_async():
    """Clean up old alert data"""
    
    async with SessionLocal() as db:
        # Clean up old notification logs (older than 90 days)
        # cleanup_count = await notification_log_manager.cleanup_old_logs(db, days=90)
        
        logger.info("Alert cleanup completed")
        
        return {
            'status': 'SUCCESS',
            'timestamp': datetime.now().isoformat()
        }
