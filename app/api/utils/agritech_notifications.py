"""
AgriTech Production Notification Service
=======================================

Enhanced notification service with production-ready features:
- Integrated SMS and Email
- Agricultural scenario templates  
- Easy credential management
- Production logging and monitoring
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import BackgroundTasks

from app.core.config import settings
from app.api.utils.notifications import (
    NotificationService as BaseNotificationService,
    NotificationChannel, 
    NotificationType,
    NotificationContent
)

# Configure logging
logger = logging.getLogger(__name__)


class AgriTechNotificationService(BaseNotificationService):
    """Enhanced notification service for AgriTech platform"""
    
    def __init__(self):
        super().__init__()
        self._log_service_status()
    
    def _log_service_status(self):
        """Log notification service initialization status"""
        email_status = "✅" if self.email_service else "❌"
        sms_status = "✅" if self.sms_service.is_available() else "❌"
        
        logger.info(f"AgriTech Notification Service initialized - Email: {email_status} SMS: {sms_status}")
    
    async def send_auction_alert(
        self,
        user_email: str,
        user_phone: Optional[str] = None,
        auction_title: str = "",
        current_bid: str = "",
        time_remaining: str = "",
        alert_type: str = "bid_placed",
        channel: NotificationChannel = NotificationChannel.BOTH
    ) -> Dict[str, Any]:
        """
        Send auction-related alerts (bidding, ending, won/lost)
        
        Args:
            user_email: User's email address
            user_phone: User's phone number (optional)
            auction_title: Name of the auction item
            current_bid: Current highest bid amount
            time_remaining: Time left in auction
            alert_type: Type of auction alert
            channel: Notification channel preference
            
        Returns:
            Dict with success status for each channel
        """
        results = {"email": False, "sms": False}
        
        # Determine notification type
        notification_type = {
            "bid_placed": NotificationType.BID_PLACED,
            "bid_outbid": NotificationType.BID_OUTBID,
            "auction_ending": NotificationType.AUCTION_ENDING,
            "auction_won": NotificationType.AUCTION_WON,
            "auction_lost": NotificationType.AUCTION_LOST,
        }.get(alert_type, NotificationType.BID_PLACED)
        
        # Email notification
        if channel in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
            try:
                email_context = {
                    "auction_title": auction_title,
                    "current_bid": current_bid,
                    "time_remaining": time_remaining,
                    "alert_type": alert_type,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                results["email"] = await self.send_email_notification(
                    recipient_email=user_email,
                    notification_type=notification_type,
                    context=email_context
                )
                
                if results["email"]:
                    logger.info(f"Auction email sent to {user_email}: {auction_title}")
                    
            except Exception as e:
                logger.error(f"Failed to send auction email to {user_email}: {e}")
        
        # SMS notification
        if channel in [NotificationChannel.SMS, NotificationChannel.BOTH] and user_phone:
            try:
                # SMS message templates
                sms_messages = {
                    "bid_placed": f"🌾 AgriTech: New bid ₹{current_bid} on '{auction_title}'. Time left: {time_remaining}",
                    "bid_outbid": f"🚨 AgriTech: You've been outbid on '{auction_title}'! Current bid: ₹{current_bid}. Bid now!",
                    "auction_ending": f"⏰ AgriTech: '{auction_title}' ending in {time_remaining}. Current bid: ₹{current_bid}",
                    "auction_won": f"🎉 AgriTech: Congratulations! You won '{auction_title}' for ₹{current_bid}!",
                    "auction_lost": f"📢 AgriTech: Auction ended. '{auction_title}' sold for ₹{current_bid}. Check new listings!"
                }
                
                sms_message = sms_messages.get(alert_type, f"🌾 AgriTech: Update on '{auction_title}' - ₹{current_bid}")
                
                results["sms"] = await self.send_sms_notification(
                    phone_number=user_phone,
                    message=sms_message
                )
                
                if results["sms"]:
                    logger.info(f"Auction SMS sent to {user_phone}: {auction_title}")
                    
            except Exception as e:
                logger.error(f"Failed to send auction SMS to {user_phone}: {e}")
        
        return results
    
    async def send_price_update(
        self,
        user_email: str,
        user_phone: Optional[str] = None,
        product_name: str = "",
        old_price: str = "",
        new_price: str = "",
        change_percent: str = "",
        market_trend: str = "stable",
        channel: NotificationChannel = NotificationChannel.BOTH
    ) -> Dict[str, Any]:
        """
        Send market price update notifications
        
        Args:
            user_email: User's email address
            user_phone: User's phone number (optional)
            product_name: Name of agricultural product
            old_price: Previous price
            new_price: Current price
            change_percent: Percentage change
            market_trend: Market trend (rising/falling/stable)
            channel: Notification channel preference
            
        Returns:
            Dict with success status for each channel
        """
        results = {"email": False, "sms": False}
        
        # Determine notification type based on trend
        notification_type = {
            "rising": NotificationType.PRICE_RISE,
            "falling": NotificationType.PRICE_DROP,
            "stable": NotificationType.PRICE_TARGET_REACHED
        }.get(market_trend, NotificationType.PRICE_RISE)
        
        # Email notification
        if channel in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
            try:
                email_context = {
                    "product_name": product_name,
                    "old_price": old_price,
                    "new_price": new_price,
                    "change_percent": change_percent,
                    "market_trend": market_trend,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                results["email"] = await self.send_email_notification(
                    recipient_email=user_email,
                    notification_type=notification_type,
                    context=email_context
                )
                
                if results["email"]:
                    logger.info(f"Price update email sent to {user_email}: {product_name}")
                    
            except Exception as e:
                logger.error(f"Failed to send price update email to {user_email}: {e}")
        
        # SMS notification
        if channel in [NotificationChannel.SMS, NotificationChannel.BOTH] and user_phone:
            try:
                # Determine emoji based on trend
                trend_emoji = {"rising": "📈", "falling": "📉", "stable": "📊"}.get(market_trend, "📊")
                
                sms_message = (
                    f"{trend_emoji} AgriTech Price Alert: {product_name} "
                    f"{old_price} → {new_price} ({change_percent})"
                )
                
                results["sms"] = await self.send_sms_notification(
                    phone_number=user_phone,
                    message=sms_message
                )
                
                if results["sms"]:
                    logger.info(f"Price update SMS sent to {user_phone}: {product_name}")
                    
            except Exception as e:
                logger.error(f"Failed to send price update SMS to {user_phone}: {e}")
        
        return results
    
    async def send_admin_alert(
        self,
        message: str,
        alert_type: str = "system",
        priority: str = "normal",
        include_developer: bool = False
    ) -> Dict[str, Any]:
        """
        Send alerts to admin contacts for system monitoring
        
        Args:
            message: Alert message
            alert_type: Type of alert (system, security, maintenance)
            priority: Alert priority (low, normal, high, urgent)
            include_developer: Whether to include developer email
            
        Returns:
            Dict with delivery status
        """
        results = {"admin_email": False, "admin_sms": False, "developer_email": False}
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Admin email
        if settings.ADMIN_EMAIL:
            try:
                results["admin_email"] = await self.send_email_notification(
                    recipient_email=settings.ADMIN_EMAIL,
                    notification_type=NotificationType.SECURITY_ALERT,
                    context={
                        "alert_type": alert_type,
                        "message": message,
                        "priority": priority,
                        "timestamp": timestamp
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send admin email alert: {e}")
        
        # Admin SMS for high priority alerts
        if settings.ADMIN_PHONE_NUMBER and priority in ["high", "urgent"]:
            try:
                priority_emoji = {"high": "🚨", "urgent": "🆘"}.get(priority, "⚠️")
                sms_message = f"{priority_emoji} AgriTech {alert_type.upper()}: {message[:100]}..."
                
                results["admin_sms"] = await self.send_sms_notification(
                    phone_number=settings.ADMIN_PHONE_NUMBER,
                    message=sms_message
                )
            except Exception as e:
                logger.error(f"Failed to send admin SMS alert: {e}")
        
        # Developer email if requested
        if include_developer and settings.DEVELOPER_EMAIL:
            try:
                results["developer_email"] = await self.send_email_notification(
                    recipient_email=settings.DEVELOPER_EMAIL,
                    notification_type=NotificationType.SYSTEM_MAINTENANCE,
                    context={
                        "alert_type": alert_type,
                        "message": message,
                        "priority": priority,
                        "timestamp": timestamp,
                        "for_developer": True
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send developer email alert: {e}")
        
        return results
    
    async def send_welcome_package(
        self,
        user_email: str,
        user_phone: Optional[str] = None,
        user_name: str = "User",
        user_type: str = "buyer"
    ) -> Dict[str, Any]:
        """
        Send comprehensive welcome package to new users
        
        Args:
            user_email: New user's email
            user_phone: New user's phone (optional)
            user_name: New user's name
            user_type: Type of user (buyer, seller, reviewer)
            
        Returns:
            Dict with delivery status
        """
        results = {"email": False, "sms": False}
        
        # Welcome email
        try:
            email_context = {
                "user_name": user_name,
                "user_type": user_type,
                "platform_name": "AgriTech Platform",
                "features": [
                    "Live auction participation",
                    "Real-time price alerts",
                    "Market trend analysis",
                    "Quality-verified products",
                    "Secure payment system"
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results["email"] = await self.send_email_notification(
                recipient_email=user_email,
                notification_type=NotificationType.WELCOME,
                context=email_context
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {e}")
        
        # Welcome SMS
        if user_phone:
            try:
                sms_message = (
                    f"🌾 Welcome to AgriTech Platform, {user_name}! "
                    f"Your {user_type} account is ready. "
                    f"Start exploring agricultural auctions and market insights!"
                )
                
                results["sms"] = await self.send_sms_notification(
                    phone_number=user_phone,
                    message=sms_message
                )
            except Exception as e:
                logger.error(f"Failed to send welcome SMS to {user_phone}: {e}")
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status for monitoring"""
        return {
            "email_service": {
                "available": self.email_service is not None,
                "configured": bool(settings.MAIL_SENDER_EMAIL and settings.MAIL_SENDER_PASSWORD),
                "sender_email": settings.MAIL_SENDER_EMAIL
            },
            "sms_service": {
                "available": self.sms_service.is_available(),
                "enabled": settings.SMS_ENABLED,
                "phone_number": settings.TWILIO_PHONE_NUMBER
            },
            "admin_contacts": {
                "admin_email": settings.ADMIN_EMAIL,
                "admin_phone": settings.ADMIN_PHONE_NUMBER,
                "developer_email": settings.DEVELOPER_EMAIL
            },
            "timestamp": datetime.now().isoformat()
        }


# Create global notification service instance
agritech_notifications = AgriTechNotificationService()


# Convenience functions for easy usage in your app
async def send_auction_notification(
    user_email: str,
    user_phone: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for auction notifications"""
    return await agritech_notifications.send_auction_alert(
        user_email=user_email,
        user_phone=user_phone,
        **kwargs
    )


async def send_price_alert(
    user_email: str,
    user_phone: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for price alerts"""
    return await agritech_notifications.send_price_update(
        user_email=user_email,
        user_phone=user_phone,
        **kwargs
    )


async def send_system_alert(message: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for system alerts"""
    return await agritech_notifications.send_admin_alert(message=message, **kwargs)


async def welcome_new_user(
    user_email: str,
    user_phone: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for welcoming new users"""
    return await agritech_notifications.send_welcome_package(
        user_email=user_email,
        user_phone=user_phone,
        **kwargs
    )
