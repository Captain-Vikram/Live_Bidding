"""
Mobile and Notification API Routes
==================================

FastAPI endpoints for mobile device management, notifications, and user experience features
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import qrcode
import io
import base64

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_optional_user
from app.db.models.accounts import User
from app.db.managers.mobile import (
    device_manager, notification_preference_manager, notification_log_manager,
    user_activity_manager, user_location_manager
)
from app.api.schemas.mobile import (
    DeviceRegistrationCreate, DeviceRegistrationResponse, DeviceListResponse,
    NotificationPreferenceUpdate, NotificationPreferenceResponse,
    NotificationHistoryResponse, NotificationAnalyticsResponse,
    PushNotificationSend, PushNotificationResponse,
    UserActivityCreate, UserActivityResponse, UserActivitySummaryResponse,
    UserLocationCreate, UserLocationResponse, LocationListResponse,
    PWAManifestResponse, AppConfigResponse, QRCodeGenerateRequest, QRCodeResponse,
    MobileSearchRequest, RecommendationRequest, RecommendationResponse,
    PerformanceMetrics, PerformanceMetricsResponse
)

router = APIRouter(prefix="/mobile", tags=["Mobile & Notifications"])


# ===== DEVICE REGISTRATION ENDPOINTS =====

@router.post("/devices/register", response_model=DeviceRegistrationResponse)
async def register_device(
    device_data: DeviceRegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a mobile device for push notifications"""
    
    try:
        device = await device_manager.register_device(
            db=db,
            user_id=current_user.id,
            device_token=device_data.device_token,
            device_type=device_data.device_type,
            device_info=device_data.device_info,
            app_version=device_data.app_version,
            os_version=device_data.os_version
        )
        return device
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register device: {str(e)}"
        )


@router.get("/devices", response_model=DeviceListResponse)
async def get_user_devices(
    active_only: bool = Query(True, description="Return only active devices"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all registered devices for the current user"""
    
    try:
        devices = await device_manager.get_user_devices(
            db=db,
            user_id=current_user.id,
            active_only=active_only
        )
        
        return DeviceListResponse(
            devices=devices,
            total=len(devices)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve devices: {str(e)}"
        )


@router.delete("/devices/{device_token}")
async def deactivate_device(
    device_token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a device registration"""
    
    try:
        success = await device_manager.deactivate_device(
            db=db,
            device_token=device_token,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return {"message": "Device deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deactivate device: {str(e)}"
        )


# ===== NOTIFICATION PREFERENCE ENDPOINTS =====

@router.get("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user notification preferences"""
    
    try:
        preferences = await notification_preference_manager.get_or_create_preferences(
            db=db,
            user_id=current_user.id
        )
        return preferences
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve preferences: {str(e)}"
        )


@router.put("/notifications/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user notification preferences"""
    
    try:
        updates = preferences_data.dict(exclude_unset=True)
        preferences = await notification_preference_manager.update_preferences(
            db=db,
            user_id=current_user.id,
            **updates
        )
        return preferences
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.get("/notifications/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to retrieve"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification history for the current user"""
    
    try:
        notifications = await notification_log_manager.get_user_notification_history(
            db=db,
            user_id=current_user.id,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset
        )
        
        has_more = len(notifications) > limit
        if has_more:
            notifications = notifications[:-1]  # Remove the extra one
        
        return NotificationHistoryResponse(
            notifications=notifications,
            total=len(notifications),
            has_more=has_more
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve notification history: {str(e)}"
        )


@router.post("/notifications/mark-clicked/{notification_id}")
async def mark_notification_clicked(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as clicked"""
    
    try:
        success = await notification_log_manager.mark_clicked(
            db=db,
            log_id=notification_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as clicked"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to mark notification: {str(e)}"
        )


# ===== USER ACTIVITY TRACKING =====

@router.post("/activity/track", response_model=UserActivityResponse)
async def track_user_activity(
    activity_data: UserActivityCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Track user activity for analytics and recommendations"""
    
    try:
        activity = await user_activity_manager.track_activity(
            db=db,
            user_id=current_user.id if current_user else None,
            activity_type=activity_data.activity_type,
            resource_type=activity_data.resource_type,
            resource_id=activity_data.resource_id,
            data=activity_data.data,
            session_id=request.session.get("session_id") if hasattr(request, "session") else None,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        return activity
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to track activity: {str(e)}"
        )


@router.get("/activity/summary", response_model=UserActivitySummaryResponse)
async def get_activity_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days for summary"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user activity summary"""
    
    try:
        summary = await user_activity_manager.get_user_activity_summary(
            db=db,
            user_id=current_user.id,
            days=days
        )
        
        return UserActivitySummaryResponse(
            activity_counts=summary["activity_counts"],
            top_viewed_resources=summary["top_viewed_resources"],
            period_days=days
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get activity summary: {str(e)}"
        )


# ===== LOCATION MANAGEMENT =====

@router.post("/locations", response_model=UserLocationResponse)
async def save_user_location(
    location_data: UserLocationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save user location"""
    
    try:
        location = await user_location_manager.save_location(
            db=db,
            user_id=current_user.id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            accuracy=location_data.accuracy,
            address=location_data.address,
            city=location_data.city,
            state=location_data.state,
            country=location_data.country,
            postal_code=location_data.postal_code,
            location_type=location_data.location_type,
            is_primary=location_data.is_primary
        )
        return location
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save location: {str(e)}"
        )


@router.get("/locations", response_model=LocationListResponse)
async def get_user_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all user locations"""
    
    try:
        locations = await user_location_manager.get_user_locations(
            db=db,
            user_id=current_user.id
        )
        
        return LocationListResponse(
            locations=locations,
            total=len(locations)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve locations: {str(e)}"
        )


# ===== PWA AND APP CONFIGURATION =====

@router.get("/pwa/manifest", response_model=PWAManifestResponse)
async def get_pwa_manifest():
    """Get PWA manifest for progressive web app"""
    
    return PWAManifestResponse(
        name="AgriTech Platform",
        short_name="AgriTech",
        description="Agricultural technology and commodity trading platform",
        start_url="/",
        display="standalone",
        background_color="#ffffff",
        theme_color="#2563eb",
        orientation="portrait",
        icons=[
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    )


@router.get("/app/config", response_model=AppConfigResponse)
async def get_app_config():
    """Get mobile app configuration"""
    
    return AppConfigResponse(
        api_base_url="https://api.agritech.com/api/v6",
        websocket_url="wss://api.agritech.com/ws",
        features={
            "real_time_trading": True,
            "price_tracking": True,
            "push_notifications": True,
            "location_services": True,
            "offline_mode": True,
            "qr_code_scanner": True
        },
        version="6.0.0",
        minimum_app_version="5.0.0",
        update_required=False,
        maintenance_mode=False
    )


@router.post("/qr/generate", response_model=QRCodeResponse)
async def generate_qr_code(
    qr_data: QRCodeGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate QR code for quick access"""
    
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f"ERROR_CORRECT_{qr_data.error_correction}"),
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data.data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        qr_code_url = f"data:image/png;base64,{img_base64}"
        
        return QRCodeResponse(
            qr_code_url=qr_code_url,
            data=qr_data.data,
            expires_at=None  # QR codes don't expire by default
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate QR code: {str(e)}"
        )


# ===== PERFORMANCE MONITORING =====

@router.post("/performance/metrics", response_model=PerformanceMetricsResponse)
async def submit_performance_metrics(
    metrics: PerformanceMetrics,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit mobile app performance metrics"""
    
    try:
        # Track performance metrics as user activity
        await user_activity_manager.track_activity(
            db=db,
            user_id=current_user.id if current_user else None,
            activity_type="performance_metrics",
            data=metrics.dict()
        )
        
        # Generate recommendations based on metrics
        recommendations = []
        if metrics.memory_usage_mb and metrics.memory_usage_mb > 500:
            recommendations.append("Consider clearing app cache to improve performance")
        
        if metrics.app_launch_time and metrics.app_launch_time > 3.0:
            recommendations.append("App launch time is high, try restarting the app")
        
        if metrics.crash_count > 0:
            recommendations.append("App crashes detected, please update to the latest version")
        
        return PerformanceMetricsResponse(
            message="Performance metrics recorded successfully",
            metrics_recorded=True,
            recommendations=recommendations if recommendations else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record metrics: {str(e)}"
        )


# ===== ADMIN ENDPOINTS =====

@router.get("/admin/notifications/analytics", response_model=NotificationAnalyticsResponse)
async def get_notification_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notification analytics (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        analytics = await notification_log_manager.get_notification_analytics(
            db=db,
            days=days
        )
        return NotificationAnalyticsResponse(**analytics)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.post("/admin/devices/cleanup")
async def cleanup_inactive_devices(
    days: int = Query(30, ge=1, le=365, description="Days of inactivity before cleanup"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cleanup inactive devices (admin only)"""
    
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        deleted_count = await device_manager.cleanup_inactive_devices(db=db, days=days)
        return {
            "message": f"Cleaned up {deleted_count} inactive devices",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cleanup devices: {str(e)}"
        )


# Health check endpoint
@router.get("/health")
async def mobile_service_health():
    """Health check for mobile service"""
    return {
        "status": "healthy",
        "service": "mobile-notifications",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "device_registration",
            "push_notifications", 
            "user_preferences",
            "activity_tracking",
            "location_services",
            "qr_code_generation",
            "pwa_support"
        ]
    }
