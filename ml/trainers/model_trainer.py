"""
Model Training and Data Processing
=================================

Automated training pipeline for commodity price prediction models
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import SessionLocal
from app.db.models.price_tracking import PriceHistory
from app.db.models.listings import CommodityListing
from ml.prediction_models import model_manager
import pandas as pd

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Handles training of ML models with price history data
    """
    
    def __init__(self):
        self.min_training_samples = 30
        self.training_window_days = 365  # Use last year of data for training
    
    async def get_commodity_price_data(self, db: AsyncSession, commodity_slug: str) -> List[Dict]:
        """
        Fetch price history data for a specific commodity
        """
        try:
            # Get commodity listing
            stmt = select(CommodityListing).where(CommodityListing.slug == commodity_slug)
            result = await db.execute(stmt)
            commodity = result.scalar_one_or_none()
            
            if not commodity:
                logger.warning(f"Commodity not found: {commodity_slug}")
                return []
            
            # Get price history for the last year
            cutoff_date = datetime.utcnow() - timedelta(days=self.training_window_days)
            
            stmt = select(PriceHistory).where(
                and_(
                    PriceHistory.commodity_id == commodity.id,
                    PriceHistory.price_date >= cutoff_date
                )
            ).order_by(PriceHistory.price_date)
            
            result = await db.execute(stmt)
            price_records = result.scalars().all()
            
            # Convert to training format
            training_data = []
            for record in price_records:
                training_data.append({
                    'price_date': record.price_date.isoformat(),
                    'price': float(record.price),
                    'market_activity': float(record.extra_data.get('market_activity', 1.0)),
                    'supply_demand_ratio': float(record.extra_data.get('supply_demand_ratio', 1.0)),
                    'commodity_id': str(record.commodity_id)
                })
            
            logger.info(f"Retrieved {len(training_data)} price records for {commodity_slug}")
            return training_data
            
        except Exception as e:
            logger.error(f"Failed to get price data for {commodity_slug}: {str(e)}")
            return []
    
    async def get_all_commodities_data(self, db: AsyncSession) -> Dict[str, List[Dict]]:
        """
        Get price data for all commodities
        """
        try:
            # Get all commodity listings
            stmt = select(CommodityListing).where(CommodityListing.active == True)
            result = await db.execute(stmt)
            commodities = result.scalars().all()
            
            commodity_data = {}
            
            for commodity in commodities:
                price_data = await self.get_commodity_price_data(db, commodity.slug)
                if len(price_data) >= self.min_training_samples:
                    commodity_data[commodity.slug] = price_data
                else:
                    logger.warning(f"Insufficient data for {commodity.slug}: {len(price_data)} samples")
            
            logger.info(f"Collected data for {len(commodity_data)} commodities")
            return commodity_data
            
        except Exception as e:
            logger.error(f"Failed to get commodities data: {str(e)}")
            return {}
    
    async def train_commodity_model(self, commodity_slug: str) -> Dict:
        """
        Train model for a specific commodity
        """
        try:
            async with SessionLocal() as db:
                price_data = await self.get_commodity_price_data(db, commodity_slug)
                
                if len(price_data) < self.min_training_samples:
                    return {
                        "error": f"Insufficient data: {len(price_data)} samples (minimum: {self.min_training_samples})"
                    }
                
                # Get model and train
                model = model_manager.get_model(commodity_slug)
                result = model.train(price_data)
                
                logger.info(f"Training completed for {commodity_slug}")
                return result
                
        except Exception as e:
            logger.error(f"Training failed for {commodity_slug}: {str(e)}")
            return {"error": str(e)}
    
    async def train_all_models(self) -> Dict:
        """
        Train models for all commodities with sufficient data
        """
        try:
            async with SessionLocal() as db:
                commodity_data = await self.get_all_commodities_data(db)
                
                if not commodity_data:
                    return {"error": "No commodities with sufficient data found"}
                
                # Train all models
                training_results = {}
                
                for commodity_slug, price_data in commodity_data.items():
                    logger.info(f"Training model for {commodity_slug}...")
                    
                    model = model_manager.get_model(commodity_slug)
                    result = model.train(price_data)
                    training_results[commodity_slug] = result
                    
                    # Log training results
                    if result.get("success"):
                        metrics = result.get("metrics", {})
                        logger.info(f"✅ {commodity_slug}: R² = {metrics.get('r2', 0):.3f}, RMSE = {metrics.get('rmse', 0):.2f}")
                    else:
                        logger.error(f"❌ {commodity_slug}: {result.get('error', 'Unknown error')}")
                
                # Summary
                successful_models = sum(1 for r in training_results.values() if r.get("success"))
                
                summary = {
                    "total_commodities": len(training_results),
                    "successful_models": successful_models,
                    "failed_models": len(training_results) - successful_models,
                    "training_results": training_results,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Training completed: {successful_models}/{len(training_results)} models successful")
                return summary
                
        except Exception as e:
            logger.error(f"Batch training failed: {str(e)}")
            return {"error": str(e)}
    
    async def retrain_model_if_stale(self, commodity_slug: str, max_age_days: int = 7) -> Dict:
        """
        Retrain model if it's older than specified days
        """
        try:
            model = model_manager.get_model(commodity_slug)
            
            # Check if model exists and its age
            if model.model_path.exists():
                model_age = datetime.utcnow() - datetime.fromtimestamp(model.model_path.stat().st_mtime)
                
                if model_age.days < max_age_days:
                    logger.info(f"Model for {commodity_slug} is recent ({model_age.days} days old)")
                    return {"message": "Model is recent, no retraining needed"}
            
            # Retrain the model
            logger.info(f"Retraining model for {commodity_slug}")
            return await self.train_commodity_model(commodity_slug)
            
        except Exception as e:
            logger.error(f"Retrain check failed for {commodity_slug}: {str(e)}")
            return {"error": str(e)}


class PriceDataGenerator:
    """
    Generates realistic price data for testing and development
    """
    
    def __init__(self):
        pass
    
    async def generate_historical_data(self, db: AsyncSession, commodity_slug: str, 
                                     days: int = 365, base_price: float = 100.0) -> List[Dict]:
        """
        Generate realistic historical price data for testing
        """
        try:
            import numpy as np
            
            # Get commodity
            stmt = select(CommodityListing).where(CommodityListing.slug == commodity_slug)
            result = await db.execute(stmt)
            commodity = result.scalar_one_or_none()
            
            if not commodity:
                logger.warning(f"Commodity not found: {commodity_slug}")
                return []
            
            # Generate realistic price series
            dates = []
            prices = []
            current_date = datetime.utcnow() - timedelta(days=days)
            current_price = base_price
            
            # Seasonal and trend components
            np.random.seed(42)  # For reproducible results
            
            for i in range(days):
                # Add seasonal pattern (annual cycle)
                seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 365)
                
                # Add trend (slight upward trend)
                trend_factor = 1 + (i / days) * 0.2
                
                # Add random walk component
                random_factor = 1 + np.random.normal(0, 0.05)
                
                # Calculate price
                current_price = base_price * seasonal_factor * trend_factor * random_factor
                
                # Ensure price doesn't go below a minimum
                current_price = max(current_price, base_price * 0.3)
                
                dates.append(current_date + timedelta(days=i))
                prices.append(current_price)
            
            # Create training data format
            training_data = []
            for i, (date, price) in enumerate(zip(dates, prices)):
                # Add market activity simulation
                market_activity = max(0.1, 1 + np.random.normal(0, 0.3))
                supply_demand_ratio = max(0.1, 1 + np.random.normal(0, 0.2))
                
                training_data.append({
                    'price_date': date.isoformat(),
                    'price': round(float(price), 2),
                    'market_activity': round(float(market_activity), 3),
                    'supply_demand_ratio': round(float(supply_demand_ratio), 3),
                    'commodity_id': str(commodity.id)
                })
            
            logger.info(f"Generated {len(training_data)} price records for {commodity_slug}")
            return training_data
            
        except Exception as e:
            logger.error(f"Failed to generate data for {commodity_slug}: {str(e)}")
            return []


# Global trainer instance
trainer = ModelTrainer()
data_generator = PriceDataGenerator()
