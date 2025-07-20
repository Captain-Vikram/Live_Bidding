"""
ML Recommendation Notification Service
=====================================

Intelligent notification system for ML-powered trading recommendations
Integrates with existing email/SMS notification infrastructure
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.utils.notifications import NotificationChannel, NotificationType, notification_service
from app.db.models.accounts import User
from app.db.models.listings import CommodityListing
from app.db.models.price_tracking import AlertSubscription, NotificationChannel as DBNotificationChannel
from ml.recommendations import recommendation_engine

logger = logging.getLogger(__name__)


class MLNotificationService:
    """
    Service for sending ML-powered recommendation notifications
    """
    
    def __init__(self):
        self.min_confidence_for_notification = 0.75  # Only notify for high-confidence recommendations
        self.notification_cooldown_hours = 6  # Don't spam users
    
    async def send_high_confidence_recommendations(self, db: AsyncSession) -> Dict:
        """
        Send notifications for high-confidence ML recommendations to subscribed users
        """
        try:
            # Get all users who have opted in for ML recommendation notifications
            users_stmt = select(User).where(User.is_active == True)
            result = await db.execute(users_stmt)
            active_users = result.scalars().all()
            
            notification_results = []
            
            for user in active_users:
                # Check if user has ML notification preferences enabled
                if not await self._should_notify_user(db, user.id):
                    continue
                
                # Get personalized recommendations for the user
                user_recommendations = await recommendation_engine.get_portfolio_recommendations(
                    db, str(user.id)
                )
                
                if not user_recommendations.get("success"):
                    continue
                
                # Filter for high-confidence recommendations
                high_confidence_recs = [
                    rec for rec in user_recommendations.get("recommendations", [])
                    if rec.get("confidence", 0) >= self.min_confidence_for_notification
                ]
                
                if not high_confidence_recs:
                    continue
                
                # Send notification
                notification_sent = await self._send_user_recommendation_notification(
                    db, user, high_confidence_recs[:3]  # Top 3 recommendations
                )
                
                notification_results.append({
                    "user_id": str(user.id),
                    "email": user.email,
                    "recommendations_count": len(high_confidence_recs),
                    "notification_sent": notification_sent
                })
            
            return {
                "success": True,
                "notifications_sent": len([r for r in notification_results if r["notification_sent"]]),
                "total_users_processed": len(notification_results),
                "results": notification_results
            }
            
        except Exception as e:
            logger.error(f"Error sending ML recommendation notifications: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_market_alert_notification(self, db: AsyncSession) -> Dict:
        """
        Send market-wide alerts for significant market movements detected by ML
        """
        try:
            # Get market overview
            market_overview = await recommendation_engine.get_market_overview(db)
            
            if not market_overview.get("success"):
                return {"success": False, "error": "Failed to get market overview"}
            
            # Check for significant market conditions
            market_sentiment = market_overview.get("market_sentiment", {})
            buy_percentage = market_sentiment.get("buy_percentage", 0)
            sell_percentage = market_sentiment.get("sell_percentage", 0)
            
            # Determine if market alert is needed
            alert_needed = False
            alert_type = None
            
            if buy_percentage > 70:
                alert_needed = True
                alert_type = "bullish_market"
            elif sell_percentage > 70:
                alert_needed = True
                alert_type = "bearish_market"
            elif buy_percentage > 80 or sell_percentage > 80:
                alert_needed = True
                alert_type = "extreme_market"
            
            if not alert_needed:
                return {"success": True, "alert_sent": False, "reason": "No significant market conditions"}
            
            # Get users subscribed to market alerts
            market_alert_users = await self._get_market_alert_subscribers(db)
            
            notifications_sent = 0
            for user in market_alert_users:
                notification_sent = await self._send_market_alert_notification(
                    db, user, alert_type, market_overview
                )
                if notification_sent:
                    notifications_sent += 1
            
            return {
                "success": True,
                "alert_sent": True,
                "alert_type": alert_type,
                "notifications_sent": notifications_sent,
                "market_sentiment": market_sentiment
            }
            
        except Exception as e:
            logger.error(f"Error sending market alert notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _should_notify_user(self, db: AsyncSession, user_id: str) -> bool:
        """
        Check if user should receive ML recommendation notifications
        """
        try:
            # Check if user has any alert subscriptions (indicates interest in notifications)
            stmt = select(AlertSubscription).where(
                and_(
                    AlertSubscription.user_id == user_id,
                    AlertSubscription.active == True
                )
            )
            result = await db.execute(stmt)
            alert_subs = result.scalars().all()
            
            # Only notify users who have shown interest in alerts
            return len(alert_subs) > 0
            
        except Exception as e:
            logger.error(f"Error checking user notification preferences: {e}")
            return False
    
    async def _send_user_recommendation_notification(
        self, 
        db: AsyncSession, 
        user: User, 
        recommendations: List[Dict]
    ) -> bool:
        """
        Send personalized recommendation notification to a user
        """
        try:
            # Prepare email content
            subject = "🎯 High-Confidence Trading Recommendations Available"
            
            # Create recommendation summary
            rec_summary = []
            for rec in recommendations:
                confidence_pct = int(rec.get("confidence", 0) * 100)
                rec_summary.append(
                    f"• {rec.get('commodity_slug', '').upper()}: "
                    f"{rec.get('suggestion', 'HOLD')} "
                    f"(₹{rec.get('current_price', 0):.2f}, "
                    f"{confidence_pct}% confidence)"
                )
            
            email_content = f"""
            Dear {user.first_name},
            
            Our AI system has identified high-confidence trading opportunities for you:
            
            {chr(10).join(rec_summary)}
            
            These recommendations are based on advanced ML analysis of price patterns, 
            market trends, and historical data.
            
            Important: These are suggestions only. Please conduct your own research 
            before making any trading decisions.
            
            Best regards,
            AgriTech Trading Platform
            """
            
            # Send via existing notification system
            await notification_service.send_notification(
                db=db,
                user_id=int(user.id),
                notification_type=NotificationType.ML_RECOMMENDATION,
                context={
                    "name": user.first_name,
                    "recommendations_count": len(recommendations),
                    "recommendations": recommendations,
                    "platform_url": "https://agritech-platform.com",  # Replace with actual URL
                    "unsubscribe_url": "https://agritech-platform.com/unsubscribe"
                },
                background_tasks=None
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending user recommendation notification: {e}")
            return False
    
    async def _send_market_alert_notification(
        self, 
        db: AsyncSession, 
        user: User, 
        alert_type: str, 
        market_data: Dict
    ) -> bool:
        """
        Send market-wide alert notification
        """
        try:
            alert_messages = {
                "bullish_market": "📈 Strong bullish signals detected across the market!",
                "bearish_market": "📉 Caution: Bearish trends identified in the market.",
                "extreme_market": "⚠️ Extreme market conditions detected!"
            }
            
            subject = f"Market Alert: {alert_messages.get(alert_type, 'Market Update')}"
            
            sentiment = market_data.get("market_sentiment", {})
            buy_pct = int(sentiment.get("buy_percentage", 0))
            sell_pct = int(sentiment.get("sell_percentage", 0))
            
            message = f"""
            Dear {user.first_name},
            
            {alert_messages.get(alert_type)}
            
            Market Overview:
            • Buy Signals: {buy_pct}%
            • Sell Signals: {sell_pct}%
            • Total Commodities Analyzed: {market_data.get('total_analyzed', 0)}
            
            This is an automated alert based on ML analysis of market conditions.
            
            Stay informed and trade wisely!
            
            AgriTech Trading Platform
            """
            
            await notification_service.send_notification(
                db=db,
                user_id=int(user.id),
                notification_type=NotificationType.MARKET_ALERT,
                context={
                    "name": user.first_name,
                    "alert_type": alert_type,
                    "buy_percentage": int(sentiment.get("buy_percentage", 0)),
                    "sell_percentage": int(sentiment.get("sell_percentage", 0)),
                    "total_analyzed": market_data.get("total_analyzed", 0),
                    "market_sentiment": alert_type.replace("_", " ").title(),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    "top_opportunities": market_data.get("top_buy_opportunities", [])[:3],
                    "platform_url": "https://agritech-platform.com",
                    "unsubscribe_url": "https://agritech-platform.com/unsubscribe"
                },
                background_tasks=None
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending market alert notification: {e}")
            return False
    
    async def _get_market_alert_subscribers(self, db: AsyncSession) -> List[User]:
        """
        Get users who are subscribed to market-wide alerts
        """
        try:
            # Get users who have alert subscriptions (indicates interest in market updates)
            stmt = select(User).join(AlertSubscription).where(
                and_(
                    User.is_active == True,
                    AlertSubscription.active == True
                )
            ).distinct()
            
            result = await db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting market alert subscribers: {e}")
            return []


# Global ML notification service instance
ml_notification_service = MLNotificationService()


# Helper functions for easy integration with Celery tasks
async def send_daily_ml_recommendations():
    """
    Helper function to send daily ML recommendations
    """
    from app.core.database import SessionLocal
    
    async with SessionLocal() as db:
        return await ml_notification_service.send_high_confidence_recommendations(db)


async def send_market_alerts_if_needed():
    """
    Helper function to send market alerts when conditions are met
    """
    from app.core.database import SessionLocal
    
    async with SessionLocal() as db:
        return await ml_notification_service.send_market_alert_notification(db)
