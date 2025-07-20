"""
Price Tracking API Routes
=========================

FastAPI routes for price history, alerts, and on-site notifications
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.db.models.accounts import User
from app.db.managers.price_tracking import (
    price_history_manager, 
    alert_subscription_manager,
    onsite_notification_manager,
    notification_log_manager
)
from app.api.schemas.price_tracking import (
    PriceHistoryResponse,
    PriceHistoryCreate,
    AlertSubscriptionCreate,
    AlertSubscriptionCreateEnhanced,
    AlertSubscriptionResponse,
    AlertSubscriptionResponseEnhanced,
    AlertSubscriptionListResponse,
    OnSiteNotificationResponse,
    OnSiteNotificationListResponse,
    NotificationMarkReadRequest,
    PriceStatisticsResponse,
    TrendingCommodityResponse,
    DashboardSummaryResponse
)
from app.api.schemas.base import ResponseSchema
from app.tasks.price_tasks import generate_daily_price_data
from app.tasks.alert_tasks import check_price_alerts

router = APIRouter(prefix="/price-tracking", tags=["Price Tracking"])

# Price History Endpoints

@router.get(
    "/price-history/{commodity_id}",
    summary="Get commodity price history",
    description="Retrieve historical price data for a specific commodity",
    response_model=ResponseSchema
)
async def get_commodity_price_history(
    commodity_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days of history to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """Get price history for a commodity"""
    try:
        price_history = await price_history_manager.get_commodity_price_history(
            db=db,
            commodity_id=str(commodity_id),
            days=days
        )
        
        if not price_history:
            return {
                "message": "No price history found for this commodity",
                "data": {
                    "price_history": [],
                    "commodity_id": str(commodity_id),
                    "period_days": days,
                    "total_records": 0
                }
            }
        
        return {
            "message": "Price history retrieved successfully",
            "data": {
                "price_history": [
                    {
                        "id": str(record.id),
                        "commodity_id": str(record.commodity_id),
                        "commodity_name": record.commodity.commodity_name if record.commodity else "Unknown",
                        "date": record.date.isoformat(),
                        "avg_price": float(record.avg_price),
                        "high_price": float(record.high_price),
                        "low_price": float(record.low_price),
                        "volume_kg": float(record.volume_kg),
                        "market_name": record.market_name,
                        "source": record.source
                    }
                    for record in price_history
                ],
                "commodity_id": str(commodity_id),
                "period_days": days,
                "total_records": len(price_history)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving price history: {str(e)}")

@router.get(
    "/price-statistics/{commodity_id}",
    summary="Get commodity price statistics",
    description="Get statistical analysis of commodity prices",
    response_model=ResponseSchema
)
async def get_price_statistics(
    commodity_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Period for statistics calculation"),
    db: AsyncSession = Depends(get_db)
):
    """Get price statistics for a commodity"""
    try:
        stats = await price_history_manager.get_price_statistics(
            db=db,
            commodity_id=str(commodity_id),
            days=days
        )
        
        return {
            "message": "Price statistics calculated successfully",
            "data": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")

@router.get(
    "/trending-commodities",
    summary="Get trending commodities",
    description="Get commodities with significant price changes",
    response_model=ResponseSchema
)
async def get_trending_commodities(
    limit: int = Query(10, ge=1, le=50, description="Number of trending commodities to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get trending commodities based on price changes"""
    try:
        trending = await price_history_manager.get_trending_commodities(db=db, limit=limit)
        
        return {
            "message": "Trending commodities retrieved successfully",
            "data": {
                "trending_commodities": trending,
                "analysis_date": date.today().isoformat(),
                "period_analyzed": "7 days"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trending data: {str(e)}")

# Alert Subscription Endpoints

@router.post(
    "/alert-subscriptions",
    summary="Create price alert subscription",
    description="Create a new price alert subscription for a commodity",
    status_code=201,
    response_model=ResponseSchema
)
async def create_alert_subscription(
    subscription_data: AlertSubscriptionCreateEnhanced,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert subscription"""
    try:
        # Check if user already has an alert for this commodity with same direction
        existing_subscriptions = await alert_subscription_manager.get_user_subscriptions(
            db=db, 
            user_id=str(current_user.id)
        )
        
        for existing in existing_subscriptions:
            if (existing.commodity_id == subscription_data.commodity_id and 
                existing.direction == subscription_data.direction and
                existing.is_active):
                raise HTTPException(
                    status_code=409, 
                    detail="You already have an active alert for this commodity and direction"
                )
        
        subscription = await alert_subscription_manager.create_subscription(
            db=db,
            user_id=str(current_user.id),
            subscription_data=subscription_data.dict()
        )
        
        return {
            "message": "Alert subscription created successfully",
            "data": {
                "id": str(subscription.id),
                "commodity_id": str(subscription.commodity_id),
                "threshold_price": float(subscription.threshold_price),
                "direction": subscription.direction.value,
                "is_active": subscription.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating subscription: {str(e)}")

@router.get(
    "/alert-subscriptions",
    summary="Get user's alert subscriptions",
    description="Retrieve all alert subscriptions for the current user",
    response_model=ResponseSchema
)
async def get_user_alert_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all alert subscriptions for current user"""
    try:
        subscriptions = await alert_subscription_manager.get_user_subscriptions(
            db=db, 
            user_id=str(current_user.id)
        )
        
        subscription_data = []
        for sub in subscriptions:
            subscription_data.append({
                "id": str(sub.id),
                "commodity_id": str(sub.commodity_id),
                "commodity_name": sub.commodity.commodity_name if sub.commodity else "Unknown",
                "threshold_price": float(sub.threshold_price),
                "direction": sub.direction.value,
                "threshold_pct": float(sub.threshold_pct) if sub.threshold_pct else None,
                "notify_email": sub.notify_email,
                "notify_sms": sub.notify_sms,
                "notify_push": sub.notify_push,
                "notify_onsite": getattr(sub, 'notify_onsite', True),
                "is_active": sub.is_active,
                "last_triggered": sub.last_triggered.isoformat() if sub.last_triggered else None,
                "trigger_count_today": getattr(sub, 'trigger_count_today', 0),
                "max_triggers_per_day": getattr(sub, 'max_triggers_per_day', 3),
                "created_at": sub.created_at.isoformat(),
                "updated_at": sub.updated_at.isoformat()
            })
        
        active_count = sum(1 for sub in subscriptions if sub.is_active)
        inactive_count = len(subscriptions) - active_count
        
        return {
            "message": "Alert subscriptions retrieved successfully",
            "data": {
                "subscriptions": subscription_data,
                "total_active": active_count,
                "total_inactive": inactive_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving subscriptions: {str(e)}")

@router.delete(
    "/alert-subscriptions/{subscription_id}",
    summary="Delete alert subscription",
    description="Delete (deactivate) an alert subscription",
    response_model=ResponseSchema
)
async def delete_alert_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert subscription"""
    try:
        # Verify subscription belongs to current user
        subscriptions = await alert_subscription_manager.get_user_subscriptions(
            db=db, 
            user_id=str(current_user.id)
        )
        
        subscription_exists = any(sub.id == subscription_id for sub in subscriptions)
        if not subscription_exists:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        success = await alert_subscription_manager.deactivate_subscription(
            db=db, 
            subscription_id=str(subscription_id)
        )
        
        if success:
            return {
                "message": "Alert subscription deleted successfully",
                "data": {"subscription_id": str(subscription_id)}
            }
        else:
            raise HTTPException(status_code=404, detail="Subscription not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting subscription: {str(e)}")

# On-site Notification Endpoints

@router.get(
    "/notifications",
    summary="Get user notifications",
    description="Retrieve on-site notifications for the current user",
    response_model=ResponseSchema
)
async def get_user_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get on-site notifications for current user"""
    try:
        notifications = await onsite_notification_manager.get_user_notifications(
            db=db,
            user_id=str(current_user.id),
            limit=limit,
            unread_only=unread_only
        )
        
        unread_count = await onsite_notification_manager.get_unread_count(
            db=db,
            user_id=str(current_user.id)
        )
        
        notification_data = []
        for notif in notifications:
            notification_data.append({
                "id": str(notif.id),
                "title": notif.title,
                "message": notif.message,
                "notification_type": notif.notification_type,
                "is_read": notif.is_read,
                "is_urgent": notif.is_urgent,
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "expires_at": notif.expires_at.isoformat() if notif.expires_at else None,
                "metadata": notif.metadata,
                "action_url": notif.action_url,
                "created_at": notif.created_at.isoformat()
            })
        
        return {
            "message": "Notifications retrieved successfully",
            "data": {
                "notifications": notification_data,
                "unread_count": unread_count,
                "total_count": len(notifications)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving notifications: {str(e)}")

@router.post(
    "/notifications/mark-read",
    summary="Mark notifications as read",
    description="Mark one or more notifications as read",
    response_model=ResponseSchema
)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark notifications as read"""
    try:
        marked_count = 0
        
        for notification_id in request.notification_ids:
            success = await onsite_notification_manager.mark_as_read(
                db=db,
                notification_id=notification_id,
                user_id=str(current_user.id)
            )
            if success:
                marked_count += 1
        
        return {
            "message": f"Marked {marked_count} notifications as read",
            "data": {"marked_as_read": marked_count}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notifications as read: {str(e)}")

@router.post(
    "/notifications/mark-all-read",
    summary="Mark all notifications as read",
    description="Mark all user notifications as read",
    response_model=ResponseSchema
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read"""
    try:
        marked_count = await onsite_notification_manager.mark_all_as_read(
            db=db,
            user_id=str(current_user.id)
        )
        
        return {
            "message": f"Marked {marked_count} notifications as read",
            "data": {"marked_as_read": marked_count}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking all notifications as read: {str(e)}")

# Dashboard and Summary Endpoints

@router.get(
    "/dashboard/summary",
    summary="Get dashboard summary",
    description="Get summary data for price tracking dashboard",
    response_model=ResponseSchema
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary data"""
    try:
        # Get user's alert subscriptions
        subscriptions = await alert_subscription_manager.get_user_subscriptions(
            db=db, 
            user_id=str(current_user.id)
        )
        
        # Get recent notifications
        recent_notifications = await onsite_notification_manager.get_user_notifications(
            db=db,
            user_id=str(current_user.id),
            limit=5
        )
        
        # Get trending commodities
        trending = await price_history_manager.get_trending_commodities(db=db, limit=10)
        
        trending_up = [item['commodity_name'] for item in trending if item['trend'] in ['up', 'strong_up']][:5]
        trending_down = [item['commodity_name'] for item in trending if item['trend'] in ['down', 'strong_down']][:5]
        
        notification_data = []
        for notif in recent_notifications:
            notification_data.append({
                "id": str(notif.id),
                "title": notif.title,
                "message": notif.message,
                "notification_type": notif.notification_type,
                "is_read": notif.is_read,
                "is_urgent": notif.is_urgent,
                "created_at": notif.created_at.isoformat()
            })
        
        return {
            "message": "Dashboard summary retrieved successfully",
            "data": {
                "total_commodities_tracked": len(set(sub.commodity_id for sub in subscriptions)),
                "total_active_alerts": sum(1 for sub in subscriptions if sub.is_active),
                "price_changes_today": len(trending),
                "alerts_triggered_today": 0,  # This would need to be calculated from today's alerts
                "trending_up": trending_up,
                "trending_down": trending_down,
                "recent_notifications": notification_data
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard summary: {str(e)}")

# Admin/Testing Endpoints

@router.post(
    "/admin/trigger-price-generation",
    summary="Trigger price generation (Admin)",
    description="Manually trigger price data generation task",
    response_model=ResponseSchema
)
async def trigger_price_generation(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger price generation (for testing/admin)"""
    # This could be restricted to admin users
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Trigger the Celery task
        task = generate_daily_price_data.delay()
        
        return {
            "message": "Price generation task triggered",
            "data": {
                "task_id": task.id,
                "status": "triggered"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering price generation: {str(e)}")

@router.post(
    "/admin/trigger-alert-check",
    summary="Trigger alert check (Admin)",
    description="Manually trigger alert checking task",
    response_model=ResponseSchema
)
async def trigger_alert_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger alert checking (for testing/admin)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Trigger the Celery task
        task = check_price_alerts.delay()
        
        return {
            "message": "Alert check task triggered",
            "data": {
                "task_id": task.id,
                "status": "triggered"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering alert check: {str(e)}")

# Unread notification count endpoint (for navbar badge)
@router.get(
    "/notifications/unread-count",
    summary="Get unread notification count",
    description="Get count of unread notifications for navbar badge",
    response_model=ResponseSchema
)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get unread notification count"""
    try:
        unread_count = await onsite_notification_manager.get_unread_count(
            db=db,
            user_id=str(current_user.id)
        )
        
        return {
            "message": "Unread count retrieved successfully",
            "data": {"unread_count": unread_count}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving unread count: {str(e)}")

# Health check endpoint
@router.get("/health")
async def price_tracking_health():
    """Health check for price tracking service"""
    return {
        "status": "healthy",
        "service": "price-tracking",
        "timestamp": date.today().isoformat()
    }
