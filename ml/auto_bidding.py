"""
ML-Powered Recommendations System
=================================

Intelligent trading recommendations based on ML predictions (without auto-bidding)
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from decimal import Decimal

from app.core.database import SessionLocal
from app.db.models.accounts import User
from app.db.models.listings import CommodityListing
from app.db.models.price_tracking import AlertSubscription
from ml.prediction_models import model_manager

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Handles ML-powered trading recommendations (no auto-bidding)
    """
    
    def __init__(self):
        self.min_confidence_threshold = 0.6
        self.min_data_points = 10
    
    async def get_commodity_recommendation(self, db: AsyncSession, commodity_slug: str) -> Dict:
        """
        Get ML-powered trading recommendation for a specific commodity
        """
        try:
            # Get commodity
            stmt = select(CommodityListing).where(CommodityListing.slug == commodity_slug)
            result = await db.execute(stmt)
            commodity = result.scalar_one_or_none()
            
            if not commodity:
                return {"error": "Commodity not found"}
            
            # Get ML model for the commodity
            model = model_manager.get_model(commodity.slug)
            
            # Get recent price data for prediction
            from app.db.managers.price_tracking import price_history_manager
            recent_data = await price_history_manager.get_recent_prices(db, commodity.id, days=60)
            
            if len(recent_data) < self.min_data_points:
                return {
                    "error": "Insufficient price data for reliable prediction",
                    "data_points": len(recent_data),
                    "required": self.min_data_points
                }
            
            # Convert to prediction format
            price_data = []
            for record in recent_data:
                price_data.append({
                    'price_date': record.price_date.isoformat(),
                    'price': float(record.price),
                    'market_activity': float(record.extra_data.get('market_activity', 1.0)),
                    'supply_demand_ratio': float(record.extra_data.get('supply_demand_ratio', 1.0)),
                    'commodity_id': str(record.commodity_id)
                })
            
            # Train model if not already trained or if data is old
            if not model.is_trained or self._should_retrain_model(model):
                logger.info(f"Training model for {commodity.slug}")
                training_result = model.train_model(price_data)
                
                if not training_result.get("success"):
                    return {
                        "error": "Failed to train model",
                        "details": training_result.get("error")
                    }
            
            # Get prediction
            prediction_result = model.predict(price_data, prediction_days=7)
            
            if not prediction_result.get("success"):
                return {
                    "error": "Prediction failed",
                    "details": prediction_result.get("error")
                }
            
            # Get current price and calculate historical stats
            current_price = float(commodity.price)
            predicted_price = prediction_result["predictions"][0]["predicted_price"]
            
            # Calculate historical statistics
            prices = [float(r.price) for r in recent_data]
            avg_price_30d = sum(prices[-30:]) / min(30, len(prices))
            avg_price_7d = sum(prices[-7:]) / min(7, len(prices))
            
            # Calculate volatility
            if len(prices) > 1:
                volatility = np.std(prices[-30:]) / avg_price_30d if avg_price_30d > 0 else 0
            else:
                volatility = 0
            
            # Calculate price trends
            if len(prices) >= 7:
                weekly_trend = (prices[-1] - prices[-7]) / prices[-7] if prices[-7] > 0 else 0
            else:
                weekly_trend = 0
                
            if len(prices) >= 30:
                monthly_trend = (prices[-1] - prices[-30]) / prices[-30] if prices[-30] > 0 else 0
            else:
                monthly_trend = 0
            
            historical_stats = {
                "avg_price_30d": avg_price_30d,
                "avg_price_7d": avg_price_7d,
                "volatility": volatility,
                "weekly_trend": weekly_trend,
                "monthly_trend": monthly_trend
            }
            
            # Get trading suggestion
            suggestion = model.get_trading_suggestion(current_price, predicted_price, historical_stats)
            
            # Add additional context
            return {
                "success": True,
                "commodity_slug": commodity_slug,
                "suggestion": suggestion["recommendation"],
                "confidence": suggestion["confidence"],
                "current_price": current_price,
                "predicted_price": predicted_price,
                "avg_price_30d": avg_price_30d,
                "avg_price_7d": avg_price_7d,
                "volatility": volatility,
                "weekly_trend": weekly_trend,
                "monthly_trend": monthly_trend,
                "reasoning": suggestion["reasoning"],
                "risk_level": suggestion["risk_level"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting commodity recommendation: {e}")
            return {
                "error": "Failed to generate recommendation",
                "details": str(e)
            }
    
    async def get_portfolio_recommendations(self, db: AsyncSession, user_id: str) -> Dict:
        """
        Get personalized recommendations based on user's portfolio and preferences
        """
        try:
            # Get user's active bids and watchlist
            user_commodities = await self._get_user_commodities(db, user_id)
            
            recommendations = []
            for commodity_slug in user_commodities:
                rec = await self.get_commodity_recommendation(db, commodity_slug)
                if rec.get("success"):
                    recommendations.append(rec)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            return {
                "success": True,
                "user_id": user_id,
                "recommendations": recommendations[:10],  # Top 10 recommendations
                "total_analyzed": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio recommendations: {e}")
            return {
                "error": "Failed to generate portfolio recommendations",
                "details": str(e)
            }
    
    async def get_market_overview(self, db: AsyncSession) -> Dict:
        """
        Get market-wide recommendations and trends
        """
        try:
            # Get top commodities by trading volume
            top_commodities = await self._get_top_commodities(db, limit=20)
            
            market_recommendations = []
            for commodity_slug in top_commodities:
                rec = await self.get_commodity_recommendation(db, commodity_slug)
                if rec.get("success"):
                    market_recommendations.append(rec)
            
            # Categorize recommendations
            buy_signals = [r for r in market_recommendations if r.get("suggestion") == "BUY"]
            sell_signals = [r for r in market_recommendations if r.get("suggestion") == "SELL"]
            hold_signals = [r for r in market_recommendations if r.get("suggestion") == "HOLD"]
            
            # Calculate market sentiment
            total_recs = len(market_recommendations)
            if total_recs > 0:
                market_sentiment = {
                    "buy_percentage": len(buy_signals) / total_recs * 100,
                    "sell_percentage": len(sell_signals) / total_recs * 100,
                    "hold_percentage": len(hold_signals) / total_recs * 100
                }
            else:
                market_sentiment = {"buy_percentage": 0, "sell_percentage": 0, "hold_percentage": 0}
            
            return {
                "success": True,
                "market_sentiment": market_sentiment,
                "top_buy_opportunities": sorted(buy_signals, key=lambda x: x["confidence"], reverse=True)[:5],
                "top_sell_opportunities": sorted(sell_signals, key=lambda x: x["confidence"], reverse=True)[:5],
                "total_analyzed": total_recs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {
                "error": "Failed to generate market overview",
                "details": str(e)
            }
    
    def _should_retrain_model(self, model) -> bool:
        """
        Check if model should be retrained based on age and performance
        """
        if not model.model_path.exists():
            return True
        
        # Retrain if model is older than 7 days
        model_age = datetime.now() - datetime.fromtimestamp(model.model_path.stat().st_mtime)
        if model_age > timedelta(days=7):
            return True
        
        # Retrain if model performance is poor
        if model.model_metrics.get("r2_score", 0) < 0.5:
            return True
        
        return False
    
    async def _get_user_commodities(self, db: AsyncSession, user_id: str) -> List[str]:
        """
        Get commodities relevant to user based on bids and watchlist
        """
        try:
            # Get commodities from user's bids
            from app.db.models.listings import Bid
            stmt = select(CommodityListing.slug).join(Bid).where(Bid.user_id == user_id).distinct()
            result = await db.execute(stmt)
            bid_commodities = [row[0] for row in result.fetchall()]
            
            # Get commodities from user's watchlist
            from app.db.models.listings import Watchlist
            stmt = select(CommodityListing.slug).join(Watchlist).where(Watchlist.user_id == user_id).distinct()
            result = await db.execute(stmt)
            watchlist_commodities = [row[0] for row in result.fetchall()]
            
            # Combine and deduplicate
            all_commodities = list(set(bid_commodities + watchlist_commodities))
            
            # If user has no activity, return popular commodities
            if not all_commodities:
                all_commodities = await self._get_top_commodities(db, limit=5)
            
            return all_commodities
            
        except Exception as e:
            logger.error(f"Error getting user commodities: {e}")
            return []
    
    async def _get_top_commodities(self, db: AsyncSession, limit: int = 10) -> List[str]:
        """
        Get top commodities by trading activity
        """
        try:
            stmt = select(CommodityListing.slug).where(CommodityListing.active == True).limit(limit)
            result = await db.execute(stmt)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting top commodities: {e}")
            return []


# Global recommendation engine instance
recommendation_engine = RecommendationEngine()


async def get_recommendation_for_commodity(commodity_slug: str) -> Dict:
    """
    Helper function to get recommendation for a commodity
    """
    async with SessionLocal() as db:
        return await recommendation_engine.get_commodity_recommendation(db, commodity_slug)


async def get_user_portfolio_recommendations(user_id: str) -> Dict:
    """
    Helper function to get portfolio recommendations for a user
    """
    async with SessionLocal() as db:
        return await recommendation_engine.get_portfolio_recommendations(db, user_id)


async def get_market_overview_data() -> Dict:
    """
    Helper function to get market overview
    """
    async with SessionLocal() as db:
        return await recommendation_engine.get_market_overview(db)
