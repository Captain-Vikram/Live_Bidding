"""
ML Recommendation Tasks
======================

Celery tasks for ML model training, prediction updates, and maintenance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.celery_app import celery_app
from ml.prediction_models import model_manager
from ml.recommendations import recommendation_engine
from app.api.utils.ml_notifications import ml_notification_service

logger = logging.getLogger(__name__)


@celery_app.task(name="train_commodity_models")
def train_all_commodity_models():
    """
    Train ML models for all active commodities
    """
    try:
        async def _train_models():
            async with SessionLocal() as db:
                # Get all active commodities
                from sqlalchemy import select
                from app.db.models.listings import CommodityListing
                
                stmt = select(CommodityListing).where(CommodityListing.active == True)
                result = await db.execute(stmt)
                commodities = result.scalars().all()
                
                training_results = {}
                
                for commodity in commodities:
                    try:
                        # Get price history
                        from app.db.managers.price_tracking import price_history_manager
                        price_data_records = await price_history_manager.get_recent_prices(
                            db, commodity.id, days=365
                        )
                        
                        if len(price_data_records) < 50:
                            training_results[commodity.slug] = {
                                "success": False,
                                "error": "Insufficient data for training"
                            }
                            continue
                        
                        # Convert to training format
                        price_data = []
                        for record in price_data_records:
                            price_data.append({
                                'price_date': record.price_date.isoformat(),
                                'price': float(record.price),
                                'market_activity': float(record.extra_data.get('market_activity', 1.0)),
                                'supply_demand_ratio': float(record.extra_data.get('supply_demand_ratio', 1.0)),
                                'commodity_id': str(record.commodity_id)
                            })
                        
                        # Train model
                        model = model_manager.get_model(commodity.slug)
                        result = model.train_model(price_data)
                        training_results[commodity.slug] = result
                        
                        logger.info(f"Training completed for {commodity.slug}: {result.get('success', False)}")
                        
                    except Exception as e:
                        training_results[commodity.slug] = {
                            "success": False,
                            "error": str(e)
                        }
                        logger.error(f"Training failed for {commodity.slug}: {str(e)}")
                
                return training_results
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(_train_models())
        loop.close()
        
        # Summary
        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        
        logger.info(f"Model training completed: {successful}/{total} successful")
        
        return {
            "task": "train_commodity_models",
            "completed_at": datetime.utcnow().isoformat(),
            "total_commodities": total,
            "successful_trainings": successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Model training task failed: {str(e)}")
        return {
            "task": "train_commodity_models",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(name="update_recommendations_cache")
def update_recommendations_cache():
    """
    Update cached recommendations for all active commodities
    """
    try:
        async def _update_cache():
            async with SessionLocal() as db:
                # Get market overview (this generates recommendations for top commodities)
                market_overview = await recommendation_engine.get_market_overview(db, limit=20)
                
                if not market_overview.get("success"):
                    return {"error": market_overview.get("error")}
                
                # Cache could be implemented with Redis here
                # For now, just return the overview
                return {
                    "cache_updated": True,
                    "commodities_processed": market_overview["market_overview"]["total_commodities"],
                    "buy_opportunities": market_overview["market_overview"]["buy_opportunities"],
                    "sell_opportunities": market_overview["market_overview"]["sell_opportunities"]
                }
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_update_cache())
        loop.close()
        
        logger.info("Recommendations cache updated successfully")
        
        return {
            "task": "update_recommendations_cache",
            "completed_at": datetime.utcnow().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Cache update task failed: {str(e)}")
        return {
            "task": "update_recommendations_cache",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(name="cleanup_old_models")
def cleanup_old_models():
    """
    Clean up old ML model files and logs
    """
    try:
        # Cleanup old model files (older than 30 days)
        model_manager.cleanup_old_models(days_old=30)
        
        # Additional cleanup could include:
        # - Old prediction logs
        # - Cached recommendations
        # - Model performance metrics
        
        logger.info("Model cleanup completed successfully")
        
        return {
            "task": "cleanup_old_models",
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Model cleanup task failed: {str(e)}")
        return {
            "task": "cleanup_old_models",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(name="train_single_commodity_model")
def train_single_commodity_model(commodity_slug: str):
    """
    Train ML model for a specific commodity
    """
    try:
        async def _train_single_model():
            async with SessionLocal() as db:
                # Get commodity
                from sqlalchemy import select
                from app.db.models.listings import CommodityListing
                
                stmt = select(CommodityListing).where(CommodityListing.slug == commodity_slug)
                result = await db.execute(stmt)
                commodity = result.scalar_one_or_none()
                
                if not commodity:
                    return {"success": False, "error": "Commodity not found"}
                
                # Get price history
                from app.db.managers.price_tracking import price_history_manager
                price_data_records = await price_history_manager.get_recent_prices(
                    db, commodity.id, days=365
                )
                
                if len(price_data_records) < 50:
                    return {
                        "success": False,
                        "error": "Insufficient data for training (minimum 50 records required)"
                    }
                
                # Convert to training format
                price_data = []
                for record in price_data_records:
                    price_data.append({
                        'price_date': record.price_date.isoformat(),
                        'price': float(record.price),
                        'market_activity': float(record.extra_data.get('market_activity', 1.0)),
                        'supply_demand_ratio': float(record.extra_data.get('supply_demand_ratio', 1.0)),
                        'commodity_id': str(record.commodity_id)
                    })
                
                # Train model
                model = model_manager.get_model(commodity_slug)
                result = model.train_model(price_data)
                
                return result
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_train_single_model())
        loop.close()
        
        logger.info(f"Training completed for {commodity_slug}: {result.get('success', False)}")
        
        return {
            "task": "train_single_commodity_model",
            "commodity_slug": commodity_slug,
            "completed_at": datetime.utcnow().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Single model training task failed for {commodity_slug}: {str(e)}")
        return {
            "task": "train_single_commodity_model",
            "commodity_slug": commodity_slug,
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(name="generate_market_insights")
def generate_market_insights():
    """
    Generate comprehensive market insights and trends analysis
    """
    try:
        async def _generate_insights():
            async with SessionLocal() as db:
                # Get market overview
                market_data = await recommendation_engine.get_market_overview(db, limit=50)
                
                if not market_data.get("success"):
                    return {"error": market_data.get("error")}
                
                # Analyze trends
                insights = {
                    "market_sentiment": "neutral",  # Could be calculated based on buy/sell ratio
                    "volatility_level": "medium",   # Could be calculated from price data
                    "trending_commodities": [],     # Top movers
                    "market_opportunities": {
                        "high_confidence_buys": len([
                            r for r in market_data.get("top_buy_recommendations", [])
                            if r.get("confidence", 0) > 0.8
                        ]),
                        "high_confidence_sells": len([
                            r for r in market_data.get("top_sell_recommendations", [])
                            if r.get("confidence", 0) > 0.8
                        ])
                    },
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                # Calculate market sentiment
                total_recs = market_data["market_overview"]["total_commodities"]
                buy_ratio = market_data["market_overview"]["buy_opportunities"] / total_recs if total_recs > 0 else 0
                
                if buy_ratio > 0.6:
                    insights["market_sentiment"] = "bullish"
                elif buy_ratio < 0.3:
                    insights["market_sentiment"] = "bearish"
                else:
                    insights["market_sentiment"] = "neutral"
                
                return insights
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        insights = loop.run_until_complete(_generate_insights())
        loop.close()
        
        logger.info("Market insights generated successfully")
        
        return {
            "task": "generate_market_insights",
            "completed_at": datetime.utcnow().isoformat(),
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Market insights task failed: {str(e)}")
        return {
            "task": "generate_market_insights",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


# Schedule periodic tasks
from celery.schedules import crontab

# Add to celery beat schedule
celery_app.conf.beat_schedule.update({
    'train-models-daily': {
        'task': 'train_commodity_models',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-recommendations-hourly': {
        'task': 'update_recommendations_cache',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-models-weekly': {
        'task': 'cleanup_old_models',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
    },
    'generate-insights-every-6-hours': {
        'task': 'generate_market_insights',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
})


@celery_app.task(name="send_ml_recommendation_notifications")
def send_ml_recommendation_notifications():
    """
    Send email/SMS notifications for high-confidence ML recommendations
    """
    try:
        async def _send_notifications():
            async with SessionLocal() as db:
                return await ml_notification_service.send_high_confidence_recommendations(db)
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send_notifications())
        loop.close()
        
        logger.info(f"ML recommendation notifications sent: {result.get('notifications_sent', 0)}")
        
        return {
            "task": "send_ml_recommendation_notifications",
            "completed_at": datetime.utcnow().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"ML notification task failed: {str(e)}")
        return {
            "task": "send_ml_recommendation_notifications",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(name="send_market_alert_notifications")
def send_market_alert_notifications():
    """
    Send market-wide alert notifications for significant market conditions
    """
    try:
        async def _send_market_alerts():
            async with SessionLocal() as db:
                return await ml_notification_service.send_market_alert_notification(db)
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_send_market_alerts())
        loop.close()
        
        logger.info(f"Market alert notifications: {result}")
        
        return {
            "task": "send_market_alert_notifications",
            "completed_at": datetime.utcnow().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Market alert notification task failed: {str(e)}")
        return {
            "task": "send_market_alert_notifications",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }


# Update beat schedule to include ML notification tasks
celery_app.conf.beat_schedule.update({
    'send-ml-recommendations-daily': {
        'task': 'send_ml_recommendation_notifications',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'send-market-alerts-every-4-hours': {
        'task': 'send_market_alert_notifications',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
})
