"""
Notification API Routes
======================

REST API endpoints for managing notifications in the AgriTech platform:
- Send individual notifications
- Send bulk notifications  
- Test SMS/Email services
- Get notification status
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.utils.notifications import (
    notification_service, 
    sms_service,
    NotificationType, 
    NotificationChannel,
    send_welcome_notification,
    send_bid_notification,
    send_outbid_alert,
    send_price_alert
)
from app.db.models.accounts import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Pydantic schemas
class NotificationRequest(BaseModel):
    """Request schema for sending notifications"""
    user_id: int
    notification_type: NotificationType
    channels: List[NotificationChannel] = [NotificationChannel.BOTH]
    context: Optional[Dict[str, Any]] = {}
    custom_phone: Optional[str] = None

    @validator('channels', pre=True)
    def validate_channels(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class BulkNotificationRequest(BaseModel):
    """Request schema for bulk notifications"""
    user_ids: List[int]
    notification_type: NotificationType
    channels: List[NotificationChannel] = [NotificationChannel.BOTH]
    context: Optional[Dict[str, Any]] = {}


class SMSTestRequest(BaseModel):
    """Request schema for SMS testing"""
    phone_number: str
    message: str

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic phone number validation
        cleaned = v.strip().replace(" ", "").replace("-", "")
        if not cleaned.startswith('+'):
            if cleaned.startswith('91'):
                cleaned = '+' + cleaned
            elif cleaned.startswith('0'):
                cleaned = '+91' + cleaned[1:]
            else:
                cleaned = '+91' + cleaned
        return cleaned


class BidNotificationRequest(BaseModel):
    """Request schema for bid notifications"""
    user_id: int
    product_name: str
    amount: float
    status: str = "confirmed"
    auction_url: Optional[str] = None


class OutbidAlertRequest(BaseModel):
    """Request schema for outbid alerts"""
    user_id: int
    product_name: str
    old_amount: float
    new_amount: float
    auction_url: Optional[str] = None


class PriceAlertRequest(BaseModel):
    """Request schema for price alerts"""
    user_id: int
    product_name: str
    old_price: float
    new_price: float
    location: str
    product_url: Optional[str] = None
    alert_type: str = "drop"

    @validator('alert_type')
    def validate_alert_type(cls, v):
        if v not in ['drop', 'rise']:
            raise ValueError('alert_type must be "drop" or "rise"')
        return v


# API Endpoints
@router.post("/send", summary="Send notification to user")
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send notification to a specific user via email/SMS
    
    **Usage Examples:**
    ```json
    {
        "user_id": 123,
        "notification_type": "welcome",
        "channels": ["email", "sms"],
        "context": {"name": "John Farmer"}
    }
    ```
    """
    try:
        result = await notification_service.send_notification(
            db=db,
            user_id=request.user_id,
            notification_type=request.notification_type,
            channels=request.channels,
            context=request.context,
            background_tasks=background_tasks,
            custom_phone=request.custom_phone
        )
        
        return {
            "success": True,
            "message": "Notification sent successfully",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/bulk", summary="Send bulk notifications")
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send notifications to multiple users
    
    **Perfect for:**
    - System announcements
    - Auction ending alerts
    - Price drop notifications
    """
    try:
        result = await notification_service.send_bulk_notification(
            db=db,
            user_ids=request.user_ids,
            notification_type=request.notification_type,
            channels=request.channels,
            context=request.context,
            background_tasks=background_tasks
        )
        
        return {
            "success": True,
            "message": f"Bulk notification sent to {len(request.user_ids)} users",
            "summary": {
                "successful": result["successful"],
                "failed": result["failed"],
                "total": len(request.user_ids)
            },
            "details": result["details"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk notifications: {str(e)}"
        )


@router.post("/test/sms", summary="Test SMS service")
async def test_sms_service(
    request: SMSTestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test SMS functionality with custom message
    
    **Test Message Examples:**
    - "Hello from AgriTech! SMS service is working perfectly 🌾"
    - "Test: Wheat price dropped to ₹25/kg in Delhi. Buy now!"
    """
    if not sms_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMS service is not configured or unavailable"
        )
    
    try:
        result = await sms_service.send_sms(
            phone_number=request.phone_number,
            message=request.message
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Test SMS sent successfully",
                "details": {
                    "message_sid": result["message_sid"],
                    "phone_number": result["phone_number"],
                    "status": result.get("status", "sent")
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SMS failed: {result['error']}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS test failed: {str(e)}"
        )


@router.get("/status", summary="Get notification service status")
async def get_notification_status(current_user: User = Depends(get_current_user)):
    """Check status of email and SMS services"""
    return {
        "email_service": {
            "available": True,  # Email is always available with FastAPI-Mail
            "status": "active",
            "provider": "FastAPI-Mail"
        },
        "sms_service": {
            "available": sms_service.is_available(),
            "status": "active" if sms_service.is_available() else "disabled",
            "provider": "Twilio" if sms_service.is_available() else None
        },
        "supported_channels": ["email", "sms"],
        "notification_types": [nt.value for nt in NotificationType]
    }


# Convenience endpoints for common AgriTech notifications
@router.post("/welcome", summary="Send welcome notification")
async def welcome_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send welcome notification to new user"""
    try:
        result = await send_welcome_notification(db, user_id, background_tasks)
        return {
            "success": True,
            "message": "Welcome notification sent",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send welcome notification: {str(e)}"
        )


@router.post("/bid", summary="Send bid confirmation")
async def notify_bid_placed(
    request: BidNotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send bid confirmation notification"""
    try:
        result = await send_bid_notification(
            db=db,
            user_id=request.user_id,
            product_name=request.product_name,
            amount=request.amount,
            status=request.status,
            url=request.auction_url or f"https://agritech.com/auction/{request.product_name}",
            background_tasks=background_tasks
        )
        
        return {
            "success": True,
            "message": "Bid notification sent",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bid notification: {str(e)}"
        )


@router.post("/outbid", summary="Send outbid alert")
async def notify_outbid(
    request: OutbidAlertRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send urgent outbid alert notification"""
    try:
        result = await send_outbid_alert(
            db=db,
            user_id=request.user_id,
            product_name=request.product_name,
            old_amount=request.old_amount,
            new_amount=request.new_amount,
            url=request.auction_url or f"https://agritech.com/auction/{request.product_name}",
            background_tasks=background_tasks
        )
        
        return {
            "success": True,
            "message": "Outbid alert sent",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send outbid alert: {str(e)}"
        )


@router.post("/price-alert", summary="Send price change alert")
async def notify_price_change(
    request: PriceAlertRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send price change alert (Phase 5 feature)"""
    try:
        result = await send_price_alert(
            db=db,
            user_id=request.user_id,
            product_name=request.product_name,
            old_price=request.old_price,
            new_price=request.new_price,
            location=request.location,
            url=request.product_url or f"https://agritech.com/market/{request.product_name}",
            alert_type=request.alert_type,
            background_tasks=background_tasks
        )
        
        return {
            "success": True,
            "message": "Price alert sent",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send price alert: {str(e)}"
        )


@router.get("/types", summary="Get notification types")
async def get_notification_types():
    """Get all available notification types for the AgriTech platform"""
    return {
        "notification_types": {
            # Authentication
            "welcome": "Welcome new users to AgriTech",
            "email_verification": "Email verification with OTP",
            "password_reset": "Password reset confirmation",
            
            # Auctions & Bidding
            "bid_placed": "Bid confirmation notification",
            "bid_outbid": "Alert when user is outbid",
            "auction_ending": "Auction ending soon alert",
            "auction_won": "Auction won celebration",
            
            # Price Alerts (Phase 5)
            "price_drop": "Price decrease notification",
            "price_rise": "Price increase notification",
            "price_target_reached": "Target price reached",
            
            # System
            "payment_confirmation": "Payment success confirmation",
            "system_maintenance": "System maintenance alerts"
        },
        "channels": {
            "email": "Email notifications using FastAPI-Mail",
            "sms": "SMS notifications using Twilio",
            "both": "Send via both email and SMS"
        }
    }
