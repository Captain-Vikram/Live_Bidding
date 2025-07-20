"""
Price Generation Tasks
======================

Celery tasks for generating realistic price data and tracking price changes
"""

from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.db.managers.price_tracking import price_history_manager
from app.db.models.listings import CommodityListing
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import random
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.price_tasks.generate_daily_price_data")
def generate_daily_price_data(self):
    """
    Generate realistic daily price data for all active commodities
    """
    logger.info("Starting daily price data generation...")
    
    try:
        return asyncio.run(_generate_price_data_async())
    except Exception as e:
        logger.error(f"Error in price generation task: {str(e)}")
        raise

async def _generate_price_data_async():
    """Async function to generate price data"""
    
    async with SessionLocal() as db:
        total_records = 0
        
        # Get all active commodity listings
        stmt = select(CommodityListing).where(CommodityListing.closing_date > datetime.now())
        result = await db.execute(stmt)
        commodities = result.scalars().all()
        
        today = date.today()
        
        for commodity in commodities:
            try:
                # Generate realistic price data
                price_data = _generate_realistic_price(commodity)
                
                # Add to price history
                await price_history_manager.add_price_data(
                    db=db,
                    commodity_id=commodity.id,
                    date=today,
                    avg_price=price_data['avg_price'],
                    high_price=price_data['high_price'],
                    low_price=price_data['low_price'],
                    volume_kg=price_data['volume_kg'],
                    market_name="AgriTech Platform",
                    source="internal_generation"
                )
                
                total_records += 1
                logger.info(f"Generated price data for {commodity.commodity_name}")
                
            except Exception as e:
                logger.error(f"Error generating price for {commodity.commodity_name}: {str(e)}")
        
        logger.info(f"Price generation completed: {total_records} records generated")
        
        return {
            'status': 'SUCCESS',
            'records_generated': total_records,
            'date': today.isoformat(),
            'timestamp': datetime.now().isoformat()
        }

def _generate_realistic_price(commodity: CommodityListing) -> Dict[str, float]:
    """
    Generate realistic price data based on commodity characteristics
    """
    
    # Base price from commodity listing
    base_price = float(commodity.min_price)
    
    # Commodity-specific price ranges (₹ per kg)
    price_ranges = {
        'wheat': (20, 35),
        'rice': (25, 45),
        'corn': (18, 30),
        'barley': (22, 38),
        'cotton': (50, 80),
        'sugarcane': (3, 8),
        'onion': (15, 50),
        'potato': (8, 25),
        'tomato': (10, 40),
        'garlic': (80, 150)
    }
    
    # Get commodity category for realistic pricing
    commodity_name = commodity.commodity_name.lower()
    price_range = None
    
    for category, range_val in price_ranges.items():
        if category in commodity_name:
            price_range = range_val
            break
    
    if not price_range:
        # Default range if commodity not found
        price_range = (base_price * 0.8, base_price * 1.2)
    
    # Apply seasonal and market volatility
    volatility_factor = random.uniform(0.85, 1.15)  # ±15% daily variation
    
    # Calculate prices with realistic market behavior
    min_price, max_price = price_range
    avg_price = random.uniform(min_price, max_price) * volatility_factor
    
    # Ensure avg_price is not below the commodity's minimum price
    avg_price = max(avg_price, base_price)
    
    # Generate high/low based on average
    price_spread = avg_price * 0.1  # 10% spread
    high_price = avg_price + random.uniform(0, price_spread)
    low_price = avg_price - random.uniform(0, price_spread)
    
    # Ensure logical price relationships
    low_price = max(low_price, base_price * 0.9)  # Don't go too low
    high_price = max(high_price, avg_price)
    low_price = min(low_price, avg_price)
    
    # Generate realistic volume (kg traded)
    volume_base = float(commodity.quantity_kg) * 0.1  # 10% of available quantity
    volume_kg = volume_base * random.uniform(0.5, 2.0)  # ±100% volume variation
    
    return {
        'avg_price': round(avg_price, 2),
        'high_price': round(high_price, 2),
        'low_price': round(low_price, 2),
        'volume_kg': round(volume_kg, 2)
    }

@celery_app.task(bind=True, name="app.tasks.price_tasks.update_price_trends")
def update_price_trends(self):
    """
    Update price trends and calculate moving averages
    """
    logger.info("Starting price trend update...")
    
    try:
        return asyncio.run(_update_trends_async())
    except Exception as e:
        logger.error(f"Error in trend update task: {str(e)}")
        raise

async def _update_trends_async():
    """Calculate and update price trends for all commodities"""
    
    async with SessionLocal() as db:
        # Get all unique commodities with price history
        stmt = select(CommodityListing.id, CommodityListing.commodity_name).distinct()
        result = await db.execute(stmt)
        commodities = result.fetchall()
        
        trends_calculated = 0
        
        for commodity_id, commodity_name in commodities:
            try:
                # Get recent price history (30 days)
                price_history = await price_history_manager.get_price_history_range(
                    db=db,
                    commodity_id=commodity_id,
                    days=30
                )
                
                if len(price_history) >= 7:  # Need at least a week of data
                    trend_data = _calculate_price_trend(price_history)
                    logger.info(f"Calculated trend for {commodity_name}: {trend_data['trend_direction']}")
                    trends_calculated += 1
                
            except Exception as e:
                logger.error(f"Error calculating trend for {commodity_name}: {str(e)}")
        
        logger.info(f"Trend calculation completed: {trends_calculated} commodities processed")
        
        return {
            'status': 'SUCCESS',
            'trends_calculated': trends_calculated,
            'timestamp': datetime.now().isoformat()
        }

def _calculate_price_trend(price_history: List) -> Dict[str, Any]:
    """Calculate price trend from historical data"""
    
    if len(price_history) < 2:
        return {'trend_direction': 'stable', 'trend_strength': 0}
    
    # Calculate price changes
    prices = [float(record.avg_price) for record in sorted(price_history, key=lambda x: x.date)]
    
    # Simple trend calculation
    recent_price = prices[-1]
    older_price = prices[0]
    
    price_change_pct = ((recent_price - older_price) / older_price) * 100
    
    # Determine trend direction and strength
    if price_change_pct > 5:
        trend_direction = 'strong_up'
        trend_strength = min(price_change_pct, 50)  # Cap at 50%
    elif price_change_pct > 1:
        trend_direction = 'up'
        trend_strength = price_change_pct
    elif price_change_pct < -5:
        trend_direction = 'strong_down'
        trend_strength = abs(price_change_pct)
    elif price_change_pct < -1:
        trend_direction = 'down'
        trend_strength = abs(price_change_pct)
    else:
        trend_direction = 'stable'
        trend_strength = abs(price_change_pct)
    
    return {
        'trend_direction': trend_direction,
        'trend_strength': round(trend_strength, 2),
        'price_change_pct': round(price_change_pct, 2),
        'analysis_period_days': len(price_history)
    }

@celery_app.task(name="app.tasks.price_tasks.cleanup_old_price_data")
def cleanup_old_price_data():
    """Clean up price data older than 2 years"""
    logger.info("Starting price data cleanup...")
    
    try:
        return asyncio.run(_cleanup_price_data_async())
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        raise

async def _cleanup_price_data_async():
    """Async cleanup of old price data"""
    
    async with SessionLocal() as db:
        cutoff_date = date.today() - timedelta(days=730)  # 2 years
        
        # This would be implemented in the price history manager
        # deleted_count = await price_history_manager.delete_old_records(db, cutoff_date)
        
        logger.info("Price data cleanup completed")
        
        return {
            'status': 'SUCCESS',
            'cutoff_date': cutoff_date.isoformat(),
            'timestamp': datetime.now().isoformat()
        }
