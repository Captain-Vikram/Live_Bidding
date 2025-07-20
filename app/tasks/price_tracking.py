"""
Celery Tasks for Price Tracking
===============================

Background tasks for fetching external price data and sending alerts
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp
import asyncpg

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.managers.price_tracking import price_history_manager, alert_subscription_manager
from app.api.utils.emails import send_email
from app.db.models.price_tracking import AlertDirection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "price_tracking",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.price_tracking']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    beat_schedule={
        'fetch-agmarknet-prices': {
            'task': 'app.tasks.price_tracking.fetch_agmarknet_prices',
            'schedule': 3600.0,  # Every hour
        },
        'fetch-enam-prices': {
            'task': 'app.tasks.price_tracking.fetch_enam_prices',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'check-price-alerts': {
            'task': 'app.tasks.price_tracking.check_all_price_alerts',
            'schedule': 300.0,  # Every 5 minutes
        },
        'cleanup-old-alerts': {
            'task': 'app.tasks.price_tracking.cleanup_old_alerts',
            'schedule': 86400.0,  # Daily
        }
    }
)


# Utility function to get async database session in Celery tasks
async def get_db_session() -> AsyncSession:
    """Get database session for async operations in Celery tasks"""
    async with SessionLocal() as db:
        return db


@celery_app.task(bind=True, max_retries=3)
def fetch_agmarknet_prices(self):
    """
    Fetch commodity prices from Agmarknet API
    
    This is a mock implementation - in production, you would integrate with actual Agmarknet API
    """
    try:
        logger.info("Starting Agmarknet price fetch")
        
        # Run async function in event loop
        result = asyncio.run(_fetch_agmarknet_prices_async())
        
        logger.info(f"Agmarknet price fetch completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Agmarknet price fetch failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


async def _fetch_agmarknet_prices_async():
    """Async implementation of Agmarknet price fetching"""
    
    db = await get_db_session()
    
    try:
        # Mock data - in production, this would be actual API calls
        mock_prices = [
            {
                "commodity_name": "Rice",
                "market": "Delhi",
                "avg_price": 2500.0,
                "high_price": 2600.0,
                "low_price": 2400.0,
                "volume_kg": 15000.0
            },
            {
                "commodity_name": "Wheat",
                "market": "Punjab",
                "avg_price": 2200.0,
                "high_price": 2250.0,
                "low_price": 2150.0,
                "volume_kg": 25000.0
            },
            {
                "commodity_name": "Tomato",
                "market": "Maharashtra",
                "avg_price": 3500.0,
                "high_price": 3800.0,
                "low_price": 3200.0,
                "volume_kg": 8000.0
            }
        ]
        
        updated_count = 0
        
        for price_data in mock_prices:
            # In production, you would map commodity names to IDs from your database
            # For now, we'll skip this step
            logger.info(f"Would update price for {price_data['commodity_name']}: ₹{price_data['avg_price']}")
            updated_count += 1
        
        return {
            "source": "agmarknet",
            "updated_count": updated_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in Agmarknet price fetch: {str(e)}")
        raise
    finally:
        await db.close()


@celery_app.task(bind=True, max_retries=3)
def fetch_enam_prices(self):
    """
    Fetch commodity prices from e-NAM API
    
    This is a mock implementation - in production, you would integrate with actual e-NAM API
    """
    try:
        logger.info("Starting e-NAM price fetch")
        
        result = asyncio.run(_fetch_enam_prices_async())
        
        logger.info(f"e-NAM price fetch completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"e-NAM price fetch failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


async def _fetch_enam_prices_async():
    """Async implementation of e-NAM price fetching"""
    
    db = await get_db_session()
    
    try:
        # Mock e-NAM API response
        enam_url = "https://api.enam.gov.in/v1/commodity-prices"  # Mock URL
        
        # In production, you would make actual HTTP requests
        mock_response = {
            "status": "success",
            "data": [
                {
                    "commodity": "Onion",
                    "market": "Nashik",
                    "min_price": 1500,
                    "max_price": 1800,
                    "modal_price": 1650,
                    "arrivals": 120.5
                },
                {
                    "commodity": "Potato",
                    "market": "Agra",
                    "min_price": 1200,
                    "max_price": 1400,
                    "modal_price": 1300,
                    "arrivals": 85.2
                }
            ]
        }
        
        updated_count = 0
        
        for item in mock_response["data"]:
            logger.info(f"Would update e-NAM price for {item['commodity']}: ₹{item['modal_price']}")
            updated_count += 1
        
        return {
            "source": "enam",
            "updated_count": updated_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in e-NAM price fetch: {str(e)}")
        raise
    finally:
        await db.close()


@celery_app.task(bind=True)
def check_all_price_alerts(self):
    """Check all active price alerts and send notifications"""
    try:
        logger.info("Starting price alert check")
        
        result = asyncio.run(_check_all_price_alerts_async())
        
        logger.info(f"Price alert check completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Price alert check failed: {str(exc)}")
        raise


async def _check_all_price_alerts_async():
    """Async implementation of price alert checking"""
    
    db = await get_db_session()
    
    try:
        # Get all commodities with recent price data
        today = date.today()
        
        # Mock: In production, you would query your database for commodities with recent prices
        mock_commodities = [
            {"id": "commodity-1", "name": "Rice", "current_price": 2550.0},
            {"id": "commodity-2", "name": "Wheat", "current_price": 2180.0},
            {"id": "commodity-3", "name": "Tomato", "current_price": 3600.0}
        ]
        
        alerts_sent = 0
        
        for commodity in mock_commodities:
            # Check for triggered alerts (mock implementation)
            triggered_alerts = await _check_commodity_alerts(
                db, commodity["id"], commodity["current_price"]
            )
            
            for alert in triggered_alerts:
                await _send_alert_notification(alert, commodity)
                alerts_sent += 1
        
        return {
            "alerts_checked": len(mock_commodities),
            "alerts_sent": alerts_sent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking price alerts: {str(e)}")
        raise
    finally:
        await db.close()


async def _check_commodity_alerts(db: AsyncSession, commodity_id: str, current_price: float):
    """Check alerts for a specific commodity"""
    
    # Mock implementation - in production, use alert_subscription_manager
    mock_triggered_alerts = []
    
    # Simulate some triggered alerts
    if current_price > 3500:  # High price threshold
        mock_triggered_alerts.append({
            "user_id": "user-1",
            "commodity_id": commodity_id,
            "threshold_price": 3500,
            "current_price": current_price,
            "direction": "sell",
            "notify_email": True,
            "notify_sms": False
        })
    
    return mock_triggered_alerts


async def _send_alert_notification(alert: Dict[str, Any], commodity: Dict[str, Any]):
    """Send alert notification to user"""
    
    try:
        message = f"🚨 Price Alert: {commodity['name']} has reached ₹{alert['current_price']:.2f}"
        
        if alert.get("notify_email"):
            # Mock email sending
            logger.info(f"Sending email alert to user {alert['user_id']}: {message}")
            # await send_email(...)
        
        if alert.get("notify_sms"):
            # Mock SMS sending
            logger.info(f"Sending SMS alert to user {alert['user_id']}: {message}")
            # await send_sms(...)
        
        if alert.get("notify_push"):
            # Mock push notification
            logger.info(f"Sending push notification to user {alert['user_id']}: {message}")
            # await send_push_notification(...)
            
    except Exception as e:
        logger.error(f"Failed to send alert notification: {str(e)}")


@celery_app.task
def cleanup_old_alerts():
    """Clean up old price alerts and expired subscriptions"""
    try:
        logger.info("Starting cleanup of old alerts")
        
        result = asyncio.run(_cleanup_old_alerts_async())
        
        logger.info(f"Alert cleanup completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Alert cleanup failed: {str(exc)}")
        raise


async def _cleanup_old_alerts_async():
    """Async implementation of alert cleanup"""
    
    db = await get_db_session()
    
    try:
        # Clean up alerts older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Mock cleanup - in production, delete old PriceAlert records
        logger.info(f"Would clean up alerts older than {cutoff_date}")
        
        return {
            "cleaned_alerts": 0,  # Mock count
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in alert cleanup: {str(e)}")
        raise
    finally:
        await db.close()


@celery_app.task(bind=True)
def send_price_alert_email(self, user_email: str, commodity_name: str, current_price: float, threshold_price: float):
    """Send price alert email to user"""
    try:
        subject = f"Price Alert: {commodity_name}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2E7D32;">🚨 Price Alert Triggered</h2>
            
            <div style="background-color: #E8F5E8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #1B5E20; margin-top: 0;">
                    {commodity_name}
                </h3>
                
                <p style="font-size: 18px; margin: 10px 0;">
                    <strong>Current Price:</strong> ₹{current_price:.2f}
                </p>
                
                <p style="font-size: 16px; margin: 10px 0;">
                    <strong>Your Threshold:</strong> ₹{threshold_price:.2f}
                </p>
            </div>
            
            <p>This alert was triggered because the current price has reached your threshold.</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 14px;">
                    Best regards,<br>
                    Smart Agri-Bidding Platform Team
                </p>
            </div>
        </div>
        """
        
        # Mock email sending
        logger.info(f"Sending price alert email to {user_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Content: {html_content}")
        
        return {"status": "sent", "email": user_email, "commodity": commodity_name}
        
    except Exception as exc:
        logger.error(f"Failed to send price alert email: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


# Utility task for manual price data import
@celery_app.task
def import_historical_prices(file_path: str, commodity_id: str):
    """Import historical price data from CSV file"""
    try:
        logger.info(f"Starting historical price import for commodity {commodity_id}")
        
        # Mock implementation
        # In production, you would:
        # 1. Read CSV file
        # 2. Validate data
        # 3. Insert into database
        # 4. Handle duplicates
        
        return {
            "status": "completed",
            "commodity_id": commodity_id,
            "imported_records": 100,  # Mock count
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Historical price import failed: {str(exc)}")
        raise


# Health check task
@celery_app.task
def health_check():
    """Health check task for Celery workers"""
    return {
        "status": "healthy",
        "worker": "price_tracking",
        "timestamp": datetime.utcnow().isoformat()
    }
