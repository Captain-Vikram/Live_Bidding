"""
AgriTech Notification Service
============================

Unified notification system supporting:
- Email notifications (existing FastAPI-Mail)
- SMS notifications (Twilio)
- Multi-channel alerts for auctions, price changes, and user actions
"""

import logging
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.utils.emails import send_email, sort_email
from app.db.managers.accounts import user_manager

# Configure logging
logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class NotificationType(str, Enum):
    """Types of notifications for the AgriTech platform"""
    # Authentication & Account
    WELCOME = "welcome"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_SUSPENDED = "account_suspended"
    
    # Auction & Bidding
    BID_PLACED = "bid_placed"
    BID_OUTBID = "bid_outbid"
    AUCTION_ENDING = "auction_ending"
    AUCTION_WON = "auction_won"
    AUCTION_LOST = "auction_lost"
    NEW_AUCTION = "new_auction"
    
    # Price Alerts (Phase 5)
    PRICE_DROP = "price_drop"
    PRICE_RISE = "price_rise"
    PRICE_TARGET_REACHED = "price_target_reached"
    
    # ML Recommendations (Phase 6)
    ML_RECOMMENDATION = "ml_recommendation"
    MARKET_ALERT = "market_alert"
    
    # System & General
    PAYMENT_CONFIRMATION = "payment_confirmation"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SECURITY_ALERT = "security_alert"


@dataclass
class NotificationContent:
    """Structured notification content for different channels"""
    subject: str
    email_template: Optional[str] = None
    email_context: Optional[Dict[str, Any]] = None
    sms_message: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent


class SMSService:
    """Twilio SMS service for AgriTech platform"""
    
    def __init__(self):
        self.client = None
        self.phone_number = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Twilio client if SMS is enabled"""
        if not settings.SMS_ENABLED:
            logger.info("SMS notifications disabled in configuration")
            return
            
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            logger.warning("SMS configuration incomplete - SMS notifications disabled")
            return
            
        try:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.phone_number = settings.TWILIO_PHONE_NUMBER
            logger.info("SMS service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SMS service: {e}")
    
    def is_available(self) -> bool:
        """Check if SMS service is available"""
        return self.client is not None and self.phone_number is not None
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS via Twilio
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message: SMS text content
            
        Returns:
            Dict with success status and details
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "SMS service not available",
                "message_sid": None
            }
        
        try:
            # Validate phone number format
            if not phone_number.startswith('+'):
                # Assume Indian number if no country code
                phone_number = f"+91{phone_number.lstrip('+91')}"
            
            # Send SMS
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone_number
            )
            
            logger.info(f"SMS sent successfully to {phone_number}: {message_obj.sid}")
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "phone_number": phone_number
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {phone_number}: {e}")
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}",
                "message_sid": None
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {phone_number}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "message_sid": None
            }


# Initialize SMS service
sms_service = SMSService()


class NotificationService:
    """Unified notification service for AgriTech platform"""
    
    def __init__(self):
        self.notification_templates = self._load_notification_templates()
    
    def _load_notification_templates(self) -> Dict[NotificationType, NotificationContent]:
        """Load notification templates for different types"""
        return {
            # Authentication notifications
            NotificationType.WELCOME: NotificationContent(
                subject="🌾 Welcome to AgriTech - Your Agricultural Marketplace!",
                email_template="welcome.html",
                sms_message="Welcome to AgriTech! Your account is now active. Start exploring agricultural auctions and connect with farmers nationwide."
            ),
            
            NotificationType.EMAIL_VERIFICATION: NotificationContent(
                subject="🔐 Verify Your AgriTech Account",
                email_template="email-activation.html",
                sms_message="Your AgriTech verification code: {otp}. Valid for 10 minutes. Don't share this code with anyone."
            ),
            
            NotificationType.PASSWORD_RESET: NotificationContent(
                subject="🔑 Reset Your AgriTech Password",
                email_template="password-reset.html",
                sms_message="AgriTech password reset requested. If this wasn't you, contact support immediately."
            ),
            
            # Auction notifications
            NotificationType.BID_PLACED: NotificationContent(
                subject="✅ Bid Confirmed - {product_name}",
                sms_message="Bid confirmed: ₹{amount} for {product_name}. Current status: {status}. Track at: {url}"
            ),
            
            NotificationType.BID_OUTBID: NotificationContent(
                subject="⚠️ You've been outbid on {product_name}",
                sms_message="OUTBID ALERT! Your ₹{old_amount} bid for {product_name} was exceeded. New highest: ₹{new_amount}. Bid again: {url}",
                priority="high"
            ),
            
            NotificationType.AUCTION_ENDING: NotificationContent(
                subject="⏰ Auction ending soon - {product_name}",
                sms_message="URGENT: {product_name} auction ends in {time_left}! Current bid: ₹{current_bid}. Last chance: {url}",
                priority="urgent"
            ),
            
            NotificationType.AUCTION_WON: NotificationContent(
                subject="🎉 Congratulations! You won the auction",
                sms_message="🏆 WINNER! You won {product_name} for ₹{amount}. Payment due in 24h. Details: {url}",
                priority="high"
            ),
            
            # Price alert notifications (Phase 5)
            NotificationType.PRICE_DROP: NotificationContent(
                subject="📉 Price Alert: {product_name} dropped to ₹{price}",
                sms_message="PRICE DROP! {product_name}: ₹{old_price} → ₹{new_price} ({percentage}% down) in {location}. Buy now: {url}"
            ),
            
            NotificationType.PRICE_RISE: NotificationContent(
                subject="📈 Price Alert: {product_name} increased to ₹{price}",
                sms_message="Price up! {product_name}: ₹{old_price} → ₹{new_price} ({percentage}% up) in {location}. Market trend: rising."
            ),
            
            # ML Recommendation notifications (Phase 6)
            NotificationType.ML_RECOMMENDATION: NotificationContent(
                subject="🎯 High-Confidence Trading Recommendations Available",
                email_template="ml-recommendations.html",
                sms_message="🤖 AI Trading Alert: {recommendations_count} high-confidence recommendations ready. Check your dashboard for details."
            ),
            
            NotificationType.MARKET_ALERT: NotificationContent(
                subject="📊 Market Alert: {alert_type} conditions detected",
                email_template="market-alert.html",
                sms_message="🚨 Market Alert: {alert_type} detected. {buy_percentage}% BUY signals, {sell_percentage}% SELL signals. Trade wisely!"
            ),
            
            # System notifications
            NotificationType.PAYMENT_CONFIRMATION: NotificationContent(
                subject="💰 Payment Confirmed - ₹{amount}",
                sms_message="Payment confirmed: ₹{amount} for {product_name}. Transaction ID: {txn_id}. Delivery in {days} days."
            ),
        }
    
    async def send_notification(
        self,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationType,
        channels: Union[NotificationChannel, List[NotificationChannel]] = NotificationChannel.BOTH,
        context: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None,
        custom_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send unified notification via multiple channels
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification to send
            channels: Which channels to use (email, sms, or both)
            context: Template context variables
            background_tasks: FastAPI background tasks
            custom_phone: Override user's phone number
            
        Returns:
            Dict with success status for each channel
        """
        context = context or {}
        
        # Get user details
        user = await user_manager.get_by_id(db=db, id=user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Normalize channels to list
        if isinstance(channels, NotificationChannel):
            if channels == NotificationChannel.BOTH:
                channel_list = [NotificationChannel.EMAIL, NotificationChannel.SMS]
            else:
                channel_list = [channels]
        else:
            channel_list = channels
        
        # Get notification template
        template = self.notification_templates.get(notification_type)
        if not template:
            return {"success": False, "error": f"No template for {notification_type}"}
        
        results = {"channels": {}, "success": True}
        
        # Send email notification
        if NotificationChannel.EMAIL in channel_list and user.email:
            try:
                if template.email_template:
                    # Use existing email service with template
                    email_context = {
                        "user": user,
                        "name": user.first_name,
                        **context,
                        **(template.email_context or {})
                    }
                    
                    if background_tasks:
                        background_tasks.add_task(
                            send_email,
                            template.email_template,
                            email_context,
                            template.subject.format(**context),
                            [user.email]
                        )
                        results["channels"]["email"] = {"success": True, "status": "queued"}
                    else:
                        await send_email(
                            template.email_template,
                            email_context,
                            template.subject.format(**context),
                            [user.email]
                        )
                        results["channels"]["email"] = {"success": True, "status": "sent"}
                else:
                    # Send simple email without template
                    sort_email_data = {
                        "email": [user.email],
                        "subject": template.subject.format(**context),
                        "template": template.sms_message.format(**context) if template.sms_message else "Notification from AgriTech"
                    }
                    
                    if background_tasks:
                        background_tasks.add_task(sort_email, sort_email_data)
                        results["channels"]["email"] = {"success": True, "status": "queued"}
                    else:
                        await sort_email(sort_email_data)
                        results["channels"]["email"] = {"success": True, "status": "sent"}
                        
            except Exception as e:
                logger.error(f"Email notification failed for user {user_id}: {e}")
                results["channels"]["email"] = {"success": False, "error": str(e)}
                results["success"] = False
        
        # Send SMS notification
        if NotificationChannel.SMS in channel_list:
            phone_number = custom_phone or getattr(user, 'phone_number', None)
            
            if phone_number and template.sms_message:
                try:
                    sms_message = template.sms_message.format(**context)
                    sms_result = await sms_service.send_sms(phone_number, sms_message)
                    results["channels"]["sms"] = sms_result
                    
                    if not sms_result["success"]:
                        results["success"] = False
                        
                except Exception as e:
                    logger.error(f"SMS notification failed for user {user_id}: {e}")
                    results["channels"]["sms"] = {"success": False, "error": str(e)}
                    results["success"] = False
            else:
                results["channels"]["sms"] = {
                    "success": False, 
                    "error": "No phone number or SMS template"
                }
        
        # Log notification attempt
        logger.info(f"Notification {notification_type} sent to user {user_id}: {results}")
        
        return results
    
    async def send_bulk_notification(
        self,
        db: AsyncSession,
        user_ids: List[int],
        notification_type: NotificationType,
        channels: Union[NotificationChannel, List[NotificationChannel]] = NotificationChannel.BOTH,
        context: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        """Send notification to multiple users"""
        results = {"successful": 0, "failed": 0, "details": []}
        
        for user_id in user_ids:
            try:
                result = await self.send_notification(
                    db, user_id, notification_type, channels, context, background_tasks
                )
                
                if result["success"]:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    
                results["details"].append({
                    "user_id": user_id,
                    "result": result
                })
                
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "user_id": user_id,
                    "result": {"success": False, "error": str(e)}
                })
        
        return results


# Initialize notification service
notification_service = NotificationService()


# Convenience functions for common notifications
async def send_welcome_notification(db: AsyncSession, user_id: int, background_tasks: Optional[BackgroundTasks] = None):
    """Send welcome notification to new user"""
    return await notification_service.send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.WELCOME,
        background_tasks=background_tasks
    )


async def send_bid_notification(
    db: AsyncSession,
    user_id: int, 
    product_name: str, 
    amount: float, 
    status: str,
    url: str,
    background_tasks: Optional[BackgroundTasks] = None
):
    """Send bid confirmation notification"""
    return await notification_service.send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.BID_PLACED,
        context={
            "product_name": product_name,
            "amount": amount,
            "status": status,
            "url": url
        },
        background_tasks=background_tasks
    )


async def send_outbid_alert(
    db: AsyncSession,
    user_id: int,
    product_name: str,
    old_amount: float,
    new_amount: float,
    url: str,
    background_tasks: Optional[BackgroundTasks] = None
):
    """Send urgent outbid alert"""
    return await notification_service.send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.BID_OUTBID,
        context={
            "product_name": product_name,
            "old_amount": old_amount,
            "new_amount": new_amount,
            "url": url
        },
        channels=NotificationChannel.BOTH,  # High priority - use both channels
        background_tasks=background_tasks
    )


async def send_price_alert(
    db: AsyncSession,
    user_id: int,
    product_name: str,
    old_price: float,
    new_price: float,
    location: str,
    url: str,
    alert_type: str = "drop",
    background_tasks: Optional[BackgroundTasks] = None
):
    """Send price change alert (Phase 5 feature)"""
    percentage = abs((new_price - old_price) / old_price * 100)
    
    notification_type = (
        NotificationType.PRICE_DROP if alert_type == "drop" 
        else NotificationType.PRICE_RISE
    )
    
    return await notification_service.send_notification(
        db=db,
        user_id=user_id,
        notification_type=notification_type,
        context={
            "product_name": product_name,
            "old_price": old_price,
            "new_price": new_price,
            "price": new_price,
            "percentage": f"{percentage:.1f}",
            "location": location,
            "url": url
        },
        background_tasks=background_tasks
    )
