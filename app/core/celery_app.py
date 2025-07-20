"""
Celery Application Configuration
===============================

Celery setup for background tasks including:
- Price data generation and tracking
- Alert processing and notifications
- On-site notifications for active users
"""

from celery import Celery
from app.core.config import settings
import os

# Create Celery app instance
celery_app = Celery(
    "agritech_worker",
    broker=f"redis://localhost:{settings.REDIS_PORT}/1",
    backend=f"redis://localhost:{settings.REDIS_PORT}/2",
    include=[
        "app.tasks.price_tasks",
        "app.tasks.alert_tasks", 
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.price_tasks.*": {"queue": "price_queue"},
        "app.tasks.alert_tasks.*": {"queue": "alert_queue"},
        "app.tasks.notification_tasks.*": {"queue": "notification_queue"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily price data generation (every 6 hours to simulate market updates)
        "generate-daily-prices": {
            "task": "app.tasks.price_tasks.generate_daily_price_data",
            "schedule": 60.0 * 60 * 6,  # Every 6 hours
        },
        
        # Check price alerts (every 30 minutes)
        "check-price-alerts": {
            "task": "app.tasks.alert_tasks.check_price_alerts",
            "schedule": 60.0 * settings.ALERT_CHECK_INTERVAL_MINUTES,
        },
        
        # Clean old notifications (daily)
        "cleanup-notifications": {
            "task": "app.tasks.notification_tasks.cleanup_old_notifications",
            "schedule": 60.0 * 60 * 24,  # Daily cleanup
        },
        
        # Generate price trends (every 2 hours)
        "update-price-trends": {
            "task": "app.tasks.price_tasks.update_price_trends",
            "schedule": 60.0 * 60 * 2,  # Every 2 hours
        },
    },
    
    # Task time limits
    task_soft_time_limit=60,
    task_time_limit=120,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

# Health check task
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery connectivity"""
    print(f"Request: {self.request!r}")
    return {"status": "success", "message": "Celery is working correctly"}
