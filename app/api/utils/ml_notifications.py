"""
ML Notifications Utility
========================

Utility functions for sending ML-related notifications to users
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.accounts import User
from app.db.models.general import Notification
from app.db.managers.general import notification_manager
from app.api.utils.notifications import send_push_notification, send_email_notification


class MLNotificationService:
    """Service for handling ML-related notifications"""
    
    @staticmethod
    async def send_price_alert(
        db: AsyncSession,
        user: User,
        commodity_name: str,
        current_price: float,
        predicted_price: float,
        confidence: float,
        suggestion: str
    ) -> None:
        """Send price alert notification to user"""
        
        # Calculate price change percentage
        price_change = ((predicted_price - current_price) / current_price) * 100
        
        title = f"Price Alert: {commodity_name}"
        
        if suggestion == "BUY":
            message = f"🔥 {commodity_name} is predicted to rise {price_change:.1f}% to ${predicted_price:.2f}. Consider buying now at ${current_price:.2f}!"
        elif suggestion == "SELL":
            message = f"⚠️ {commodity_name} is predicted to drop {abs(price_change):.1f}% to ${predicted_price:.2f}. Consider selling at current price ${current_price:.2f}."
        else:
            message = f"📊 {commodity_name} price stable. Current: ${current_price:.2f}, Predicted: ${predicted_price:.2f}"
        
        # Create notification in database
        await notification_manager.create_notification(
            db=db,
            user_id=user.id,
            title=title,
            message=message,
            type="PRICE_ALERT",
            metadata={
                "commodity_name": commodity_name,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "confidence": confidence,
                "suggestion": suggestion,
                "price_change_pct": price_change
            }
        )
        
        # Send push notification if user has enabled it
        if user.push_notifications_enabled:
            await send_push_notification(
                user_id=user.id,
                title=title,
                message=message,
                data={
                    "type": "price_alert",
                    "commodity": commodity_name,
                    "suggestion": suggestion
                }
            )
        
        # Send email notification if user has enabled it
        if user.email_notifications_enabled:
            await send_email_notification(
                email=user.email,
                subject=title,
                template="price_alert",
                context={
                    "user_name": user.first_name,
                    "commodity_name": commodity_name,
                    "current_price": current_price,
                    "predicted_price": predicted_price,
                    "confidence": confidence * 100,
                    "suggestion": suggestion,
                    "price_change_pct": abs(price_change)
                }
            )
    
    @staticmethod
    async def send_auto_bid_notification(
        db: AsyncSession,
        user: User,
        listing_name: str,
        bid_amount: float,
        status: str,
        reason: str = ""
    ) -> None:
        """Send auto-bid notification to user"""
        
        title = f"Auto-Bid {status.title()}: {listing_name}"
        
        if status == "placed":
            message = f"🤖 Auto-bid of ${bid_amount:.2f} placed on {listing_name}. {reason}"
        elif status == "won":
            message = f"🎉 Congratulations! Your auto-bid of ${bid_amount:.2f} won {listing_name}!"
        elif status == "outbid":
            message = f"⚡ Your auto-bid of ${bid_amount:.2f} on {listing_name} has been outbid. {reason}"
        elif status == "failed":
            message = f"❌ Auto-bid failed on {listing_name}. {reason}"
        else:
            message = f"Auto-bid update on {listing_name}: ${bid_amount:.2f} - {reason}"
        
        # Create notification in database
        await notification_manager.create_notification(
            db=db,
            user_id=user.id,
            title=title,
            message=message,
            type="AUTO_BID",
            metadata={
                "listing_name": listing_name,
                "bid_amount": bid_amount,
                "status": status,
                "reason": reason
            }
        )
        
        # Send push notification
        if user.push_notifications_enabled:
            await send_push_notification(
                user_id=user.id,
                title=title,
                message=message,
                data={
                    "type": "auto_bid",
                    "listing_name": listing_name,
                    "status": status
                }
            )
    
    @staticmethod
    async def send_market_analysis_notification(
        db: AsyncSession,
        user: User,
        market_summary: Dict[str, Any]
    ) -> None:
        """Send daily/weekly market analysis notification"""
        
        title = "📈 Market Analysis Update"
        
        trending_up = market_summary.get("trending_up", [])
        trending_down = market_summary.get("trending_down", [])
        opportunities = market_summary.get("opportunities", [])
        
        message_parts = []
        
        if trending_up:
            message_parts.append(f"📈 Rising: {', '.join(trending_up[:3])}")
        
        if trending_down:
            message_parts.append(f"📉 Falling: {', '.join(trending_down[:3])}")
        
        if opportunities:
            message_parts.append(f"💡 Opportunities: {', '.join(opportunities[:2])}")
        
        message = " | ".join(message_parts) if message_parts else "Market conditions stable"
        
        # Create notification in database
        await notification_manager.create_notification(
            db=db,
            user_id=user.id,
            title=title,
            message=message,
            type="MARKET_ANALYSIS",
            metadata=market_summary
        )
        
        # Send email notification for market analysis
        if user.email_notifications_enabled:
            await send_email_notification(
                email=user.email,
                subject=title,
                template="market_analysis",
                context={
                    "user_name": user.first_name,
                    "market_summary": market_summary,
                    "trending_up": trending_up,
                    "trending_down": trending_down,
                    "opportunities": opportunities
                }
            )
    
    @staticmethod
    async def send_model_update_notification(
        db: AsyncSession,
        user: User,
        model_name: str,
        accuracy_improvement: float,
        new_features: List[str]
    ) -> None:
        """Send notification about ML model updates"""
        
        title = f"🤖 {model_name} Model Updated"
        
        message = f"Our {model_name} model has been improved with {accuracy_improvement:.1f}% better accuracy"
        
        if new_features:
            message += f" and new features: {', '.join(new_features)}"
        
        # Create notification in database
        await notification_manager.create_notification(
            db=db,
            user_id=user.id,
            title=title,
            message=message,
            type="MODEL_UPDATE",
            metadata={
                "model_name": model_name,
                "accuracy_improvement": accuracy_improvement,
                "new_features": new_features
            }
        )
    
    @staticmethod
    async def send_trading_suggestion_notification(
        db: AsyncSession,
        user: User,
        suggestions: List[Dict[str, Any]]
    ) -> None:
        """Send trading suggestions notification"""
        
        if not suggestions:
            return
        
        title = "💡 New Trading Suggestions"
        
        # Create summary of suggestions
        buy_suggestions = [s for s in suggestions if s.get("suggestion") == "BUY"]
        sell_suggestions = [s for s in suggestions if s.get("suggestion") == "SELL"]
        
        message_parts = []
        
        if buy_suggestions:
            buy_commodities = [s.get("commodity_name", "Unknown") for s in buy_suggestions[:2]]
            message_parts.append(f"🔥 Buy: {', '.join(buy_commodities)}")
        
        if sell_suggestions:
            sell_commodities = [s.get("commodity_name", "Unknown") for s in sell_suggestions[:2]]
            message_parts.append(f"💰 Sell: {', '.join(sell_commodities)}")
        
        message = " | ".join(message_parts) if message_parts else "New trading insights available"
        
        # Create notification in database
        await notification_manager.create_notification(
            db=db,
            user_id=user.id,
            title=title,
            message=message,
            type="TRADING_SUGGESTION",
            metadata={
                "suggestions_count": len(suggestions),
                "buy_count": len(buy_suggestions),
                "sell_count": len(sell_suggestions),
                "suggestions": suggestions[:5]  # Store first 5 suggestions
            }
        )
        
        # Send push notification
        if user.push_notifications_enabled:
            await send_push_notification(
                user_id=user.id,
                title=title,
                message=message,
                data={
                    "type": "trading_suggestion",
                    "suggestions_count": len(suggestions)
                }
            )


# Convenience functions for easy access
async def notify_price_alert(db: AsyncSession, user: User, **kwargs):
    """Convenience function for price alerts"""
    await MLNotificationService.send_price_alert(db, user, **kwargs)

async def notify_auto_bid(db: AsyncSession, user: User, **kwargs):
    """Convenience function for auto-bid notifications"""
    await MLNotificationService.send_auto_bid_notification(db, user, **kwargs)

async def notify_market_analysis(db: AsyncSession, user: User, **kwargs):
    """Convenience function for market analysis notifications"""
    await MLNotificationService.send_market_analysis_notification(db, user, **kwargs)

async def notify_model_update(db: AsyncSession, user: User, **kwargs):
    """Convenience function for model update notifications"""
    await MLNotificationService.send_model_update_notification(db, user, **kwargs)

async def notify_trading_suggestions(db: AsyncSession, user: User, **kwargs):
    """Convenience function for trading suggestions notifications"""
    await MLNotificationService.send_trading_suggestion_notification(db, user, **kwargs)
