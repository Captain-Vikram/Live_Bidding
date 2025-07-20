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


# ===== PRICE HISTORY ENDPOINTS =====

@router.post("/price-history", response_model=PriceHistoryResponse)
async def add_price_data(
    price_data: PriceHistoryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add new price data for a commodity
    
    Requires admin or seller role for manual price updates
    """
    if current_user.role not in ["admin", "seller"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and sellers can add price data"
        )
    
    try:
        price_record = await price_history_manager.add_price_data(
            db=db,
            commodity_id=price_data.commodity_id,
            date=price_data.date,
            avg_price=price_data.avg_price,
            high_price=price_data.high_price,
            low_price=price_data.low_price,
            volume_kg=price_data.volume_kg,
            market_name=price_data.market_name,
            source=price_data.source
        )
        
        # Schedule alert checking in background
        background_tasks.add_task(
            check_and_send_alerts,
            commodity_id=price_data.commodity_id,
            current_price=price_data.avg_price,
            db=db
        )
        
        return price_record
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add price data: {str(e)}"
        )


@router.get("/price-history/{commodity_id}", response_model=List[PriceHistoryResponse])
async def get_price_history(
    commodity_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    start_date: Optional[date] = Query(None, description="Start date for custom range"),
    end_date: Optional[date] = Query(None, description="End date for custom range"),
    db: AsyncSession = Depends(get_db)
):
    """Get price history for a commodity"""
    
    try:
        price_history = await price_history_manager.get_price_history(
            db=db,
            commodity_id=commodity_id,
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        return price_history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve price history: {str(e)}"
        )


@router.get("/price-history/{commodity_id}/latest", response_model=PriceHistoryResponse)
async def get_latest_price(
    commodity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest price data for a commodity"""
    
    latest_price = await price_history_manager.get_latest_price(db, commodity_id)
    
    if not latest_price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price data found for this commodity"
        )
    
    return latest_price


@router.get("/price-history/{commodity_id}/statistics", response_model=PriceStatistics)
async def get_price_statistics(
    commodity_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_db)
):
    """Get price statistics for a commodity over specified period"""
    
    try:
        stats = await price_history_manager.get_price_statistics(
            db=db,
            commodity_id=commodity_id,
            days=days
        )
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price data found for statistics calculation"
            )
        
        return PriceStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate statistics: {str(e)}"
        )


@router.get("/trending", response_model=List[TrendingCommodity])
async def get_trending_commodities(
    limit: int = Query(10, ge=1, le=50, description="Number of trending commodities"),
    db: AsyncSession = Depends(get_db)
):
    """Get commodities with significant price changes"""
    
    try:
        trending = await price_history_manager.get_trending_commodities(db, limit)
        return [TrendingCommodity(**item) for item in trending]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get trending commodities: {str(e)}"
        )


@router.post("/bulk-import", response_model=dict)
async def bulk_import_prices(
    import_data: BulkPriceImport,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk import price data for a commodity"""
    
    if current_user.role not in ["admin", "seller"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and sellers can bulk import price data"
        )
    
    try:
        imported_count = 0
        failed_count = 0
        
        for price_data in import_data.price_data:
            try:
                await price_history_manager.add_price_data(
                    db=db,
                    commodity_id=import_data.commodity_id,
                    date=price_data.date,
                    avg_price=price_data.avg_price,
                    high_price=price_data.high_price,
                    low_price=price_data.low_price,
                    volume_kg=price_data.volume_kg,
                    market_name=price_data.market_name,
                    source=price_data.source
                )
                imported_count += 1
            except Exception:
                failed_count += 1
        
        # Check alerts for the latest price
        if import_data.price_data:
            latest_price = max(import_data.price_data, key=lambda x: x.date)
            background_tasks.add_task(
                check_and_send_alerts,
                commodity_id=import_data.commodity_id,
                current_price=latest_price.avg_price,
                db=db
            )
        
        return {
            "message": "Bulk import completed",
            "imported": imported_count,
            "failed": failed_count,
            "total": len(import_data.price_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bulk import failed: {str(e)}"
        )


# ===== ALERT SUBSCRIPTION ENDPOINTS =====

@router.post("/alerts/subscribe", response_model=AlertSubscriptionResponse)
async def create_alert_subscription(
    subscription_data: AlertSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new price alert subscription"""
    
    try:
        subscription = await alert_subscription_manager.create_subscription(
            db=db,
            user_id=current_user.id,
            commodity_id=subscription_data.commodity_id,
            threshold_price=subscription_data.threshold_price,
            threshold_pct=subscription_data.threshold_pct,
            direction=subscription_data.direction,
            notify_email=subscription_data.notify_email,
            notify_sms=subscription_data.notify_sms,
            notify_push=subscription_data.notify_push
        )
        return subscription
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.get("/alerts/subscriptions", response_model=List[AlertSubscriptionResponse])
async def get_user_subscriptions(
    active_only: bool = Query(True, description="Return only active subscriptions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all alert subscriptions for the current user"""
    
    try:
        subscriptions = await alert_subscription_manager.get_user_subscriptions(
            db=db,
            user_id=current_user.id,
            active_only=active_only
        )
        return subscriptions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve subscriptions: {str(e)}"
        )


@router.put("/alerts/subscriptions/{subscription_id}", response_model=AlertSubscriptionResponse)
async def update_alert_subscription(
    subscription_id: UUID,
    update_data: AlertSubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an alert subscription"""
    
    try:
        # Get existing subscription
        subscription = await alert_subscription_manager.get_by_id(db, subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        if subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own subscriptions"
            )
        
        # Update fields
        update_fields = update_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(subscription, field, value)
        
        await db.commit()
        await db.refresh(subscription)
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update subscription: {str(e)}"
        )


@router.delete("/alerts/subscriptions/{subscription_id}")
async def deactivate_alert_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate an alert subscription"""
    
    try:
        success = await alert_subscription_manager.deactivate_subscription(
            db=db,
            subscription_id=subscription_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found or already deactivated"
            )
        
        return {"message": "Subscription deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deactivate subscription: {str(e)}"
        )


# ===== EXTERNAL API ENDPOINTS =====

@router.post("/external/market-update")
async def receive_market_price_update(
    market_data: MarketPriceUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive price updates from external market APIs
    
    This endpoint would be called by external services like Agmarknet, e-NAM, etc.
    """
    
    try:
        updated_count = 0
        
        for price_data in market_data.prices:
            await price_history_manager.add_price_data(
                db=db,
                commodity_id=price_data.commodity_id,
                date=price_data.date,
                avg_price=price_data.avg_price,
                high_price=price_data.high_price,
                low_price=price_data.low_price,
                volume_kg=price_data.volume_kg,
                market_name=price_data.market_name,
                source=market_data.source
            )
            
            # Schedule alert checking
            background_tasks.add_task(
                check_and_send_alerts,
                commodity_id=price_data.commodity_id,
                current_price=price_data.avg_price,
                db=db
            )
            
            updated_count += 1
        
        return {
            "message": f"Market price update received from {market_data.source}",
            "updated_prices": updated_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process market update: {str(e)}"
        )


# ===== BACKGROUND TASKS =====

async def check_and_send_alerts(commodity_id: UUID, current_price: float, db: AsyncSession):
    """Background task to check and send price alerts"""
    
    try:
        # Get triggered subscriptions
        triggered_subscriptions = await alert_subscription_manager.check_price_alerts(
            db=db,
            commodity_id=commodity_id,
            current_price=current_price
        )
        
        # Process each triggered subscription
        for subscription in triggered_subscriptions:
            # Here you would implement actual notification sending
            # For now, we'll just log the alert
            
            alert_message = f"Price alert: {subscription.commodity.commodity_name} is now ₹{current_price:.2f}"
            
            # In a real implementation, you would:
            # 1. Send email if subscription.notify_email
            # 2. Send SMS if subscription.notify_sms  
            # 3. Send push notification if subscription.notify_push
            # 4. Create PriceAlert record in database
            
            print(f"Alert triggered for user {subscription.user_id}: {alert_message}")
            
            # Update last triggered timestamp
            subscription.last_triggered = datetime.utcnow()
            await db.commit()
    
    except Exception as e:
        print(f"Error checking alerts for commodity {commodity_id}: {str(e)}")


# Health check endpoint
@router.get("/health")
async def price_tracking_health():
    """Health check for price tracking service"""
    return {
        "status": "healthy",
        "service": "price-tracking",
        "timestamp": datetime.utcnow().isoformat()
    }
