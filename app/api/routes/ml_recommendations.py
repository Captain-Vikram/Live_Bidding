"""
ML Recommendations API Routes
============================

FastAPI endpoints for ML-powered trading suggestions and auto-bidding
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_optional_user
from app.db.models.accounts import User
from app.db.models.listings import CommodityListing
from app.db.managers.listings import listing_manager
from app.db.managers.price_tracking import price_history_manager
from ml.prediction_models import model_manager
from ml.trainers.model_trainer import trainer
from ml.auto_bidding import auto_bidding_engine

router = APIRouter(prefix="/ml-recommendations", tags=["ML Recommendations"])


# ===== PYDANTIC SCHEMAS =====

class TradingSuggestionResponse(BaseModel):
    """Trading suggestion response model"""
    suggestion: str = Field(..., description="BUY, SELL, or HOLD")
    current_price: float = Field(..., description="Current market price")
    predicted_price: float = Field(..., description="ML predicted price")
    avg_price_30d: float = Field(..., description="30-day average price")
    confidence: float = Field(..., description="ML model confidence (0-1)")
    price_change_pct: float = Field(..., description="Expected price change percentage")
    reason: str = Field(..., description="Explanation for the suggestion")
    volatility: float = Field(..., description="Price volatility measure")
    market_position: str = Field(..., description="ABOVE_AVG or BELOW_AVG")
    
    class Config:
        schema_extra = {
            "example": {
                "suggestion": "BUY",
                "current_price": 125.50,
                "predicted_price": 135.20,
                "avg_price_30d": 120.30,
                "confidence": 0.85,
                "price_change_pct": 7.72,
                "reason": "Price expected to rise significantly and currently below average",
                "volatility": 0.12,
                "market_position": "ABOVE_AVG"
            }
        }


class PricePredictionResponse(BaseModel):
    """Price prediction response model"""
    commodity_slug: str
    predictions: List[Dict[str, Any]]
    model_confidence: float
    training_samples: int
    last_updated: str
    
    class Config:
        schema_extra = {
            "example": {
                "commodity_slug": "wheat-premium",
                "predictions": [
                    {"date": "2025-07-21", "predicted_price": 135.20, "day_ahead": 1},
                    {"date": "2025-07-22", "predicted_price": 137.80, "day_ahead": 2}
                ],
                "model_confidence": 0.85,
                "training_samples": 250,
                "last_updated": "2025-07-20T10:30:00"
            }
        }


class AutoBidSubscriptionCreate(BaseModel):
    """Auto-bidding subscription creation model"""
    commodity_slug: str = Field(..., description="Commodity slug to auto-bid on")
    max_bid_amount: float = Field(..., gt=0, description="Maximum bid amount")
    strategy: str = Field("conservative", description="Bidding strategy: conservative, moderate, aggressive")
    
    class Config:
        schema_extra = {
            "example": {
                "commodity_slug": "wheat-premium",
                "max_bid_amount": 150.00,
                "strategy": "moderate"
            }
        }


class AutoBidSubscriptionResponse(BaseModel):
    """Auto-bidding subscription response model"""
    id: str
    commodity_slug: str
    commodity_name: str
    max_bid_amount: float
    strategy: str
    is_active: bool
    created_at: str


class ModelTrainingResponse(BaseModel):
    """Model training response model"""
    success: bool
    message: str
    metrics: Optional[Dict[str, Any]] = None
    training_time: Optional[str] = None


# ===== TRADING SUGGESTIONS ENDPOINTS =====

@router.get("/suggestions/{commodity_slug}", response_model=TradingSuggestionResponse)
async def get_trading_suggestion(
    commodity_slug: str,
    prediction_days: int = Query(1, ge=1, le=7, description="Days ahead for prediction"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ML-powered trading suggestion for a commodity
    
    Returns intelligent BUY/SELL/HOLD recommendation based on:
    - ML price predictions
    - Historical price analysis
    - Market volatility
    - Technical indicators
    """
    try:
        # Get commodity
        commodity = await listing_manager.get_by_slug(db, commodity_slug)
        if not commodity:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # Get ML model
        model = model_manager.get_model(commodity_slug)
        
        # Load model if not trained
        if not model.is_trained and not model._load_model():
            raise HTTPException(
                status_code=503, 
                detail="ML model not available. Please train the model first."
            )
        
        # Get recent price data
        recent_data = await price_history_manager.get_recent_prices(db, commodity.id, days=30)
        
        if len(recent_data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient price data for prediction"
            )
        
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
        
        # Get prediction
        prediction_result = model.predict(price_data, prediction_days=prediction_days)
        
        if not prediction_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Prediction failed: {prediction_result.get('error', 'Unknown error')}"
            )
        
        # Calculate historical stats
        prices = [float(r.price) for r in recent_data]
        avg_price_30d = sum(prices) / len(prices)
        volatility = (max(prices) - min(prices)) / avg_price_30d if avg_price_30d > 0 else 0
        
        historical_stats = {
            "avg_price_30d": avg_price_30d,
            "volatility": volatility
        }
        
        # Get trading suggestion
        current_price = float(commodity.price)
        predicted_price = prediction_result["predictions"][0]["predicted_price"]
        
        suggestion = model.get_trading_suggestion(current_price, predicted_price, historical_stats)
        
        if suggestion.get("error"):
            raise HTTPException(status_code=500, detail=suggestion["error"])
        
        return TradingSuggestionResponse(**suggestion)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading suggestion: {str(e)}")


@router.get("/predictions/{commodity_slug}", response_model=PricePredictionResponse)
async def get_price_predictions(
    commodity_slug: str,
    days: int = Query(7, ge=1, le=30, description="Number of days to predict"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed price predictions for a commodity
    
    Returns ML-based price forecasts for the specified number of days
    """
    try:
        # Get commodity
        commodity = await listing_manager.get_by_slug(db, commodity_slug)
        if not commodity:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # Get ML model
        model = model_manager.get_model(commodity_slug)
        
        if not model.is_trained and not model._load_model():
            raise HTTPException(
                status_code=503,
                detail="ML model not available. Please train the model first."
            )
        
        # Get recent price data
        recent_data = await price_history_manager.get_recent_prices(db, commodity.id, days=30)
        
        if len(recent_data) < 10:
            raise HTTPException(
                status_code=400,
                detail="Insufficient price data for prediction"
            )
        
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
        
        # Get predictions
        prediction_result = model.predict(price_data, prediction_days=days)
        
        if not prediction_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Prediction failed: {prediction_result.get('error', 'Unknown error')}"
            )
        
        return PricePredictionResponse(
            commodity_slug=commodity_slug,
            predictions=prediction_result["predictions"],
            model_confidence=prediction_result["model_confidence"],
            training_samples=model.model_metrics.get("training_samples", 0),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get predictions: {str(e)}")


# ===== AUTO-BIDDING ENDPOINTS =====

@router.post("/auto-bidding/subscribe")
async def create_auto_bid_subscription(
    subscription_data: AutoBidSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an auto-bidding subscription
    
    Enables automated bidding based on ML predictions and user-defined limits
    """
    try:
        # Validate strategy
        if subscription_data.strategy not in ["conservative", "moderate", "aggressive"]:
            raise HTTPException(
                status_code=400,
                detail="Strategy must be one of: conservative, moderate, aggressive"
            )
        
        result = await auto_bidding_engine.create_auto_bid_subscription(
            db=db,
            user_id=str(current_user.id),
            commodity_slug=subscription_data.commodity_slug,
            max_bid_amount=subscription_data.max_bid_amount,
            strategy=subscription_data.strategy
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"message": result["message"], "subscription_id": result["subscription_id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create auto-bid subscription: {str(e)}")


@router.get("/auto-bidding/subscriptions", response_model=List[AutoBidSubscriptionResponse])
async def get_auto_bid_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all auto-bidding subscriptions for the current user
    """
    try:
        subscriptions = await auto_bidding_engine.get_user_auto_bid_subscriptions(
            db=db, 
            user_id=str(current_user.id)
        )
        
        return [AutoBidSubscriptionResponse(**sub) for sub in subscriptions]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscriptions: {str(e)}")


@router.delete("/auto-bidding/subscriptions/{subscription_id}")
async def deactivate_auto_bid_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate an auto-bidding subscription
    """
    try:
        from app.db.managers.price_tracking import alert_subscription_manager
        from sqlalchemy import and_
        
        # Get subscription
        subscription = await alert_subscription_manager.get_by_id(db, subscription_id)
        
        if not subscription or str(subscription.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Deactivate subscription
        await alert_subscription_manager.update(db, subscription, {"is_active": False})
        
        return {"message": "Auto-bidding subscription deactivated"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate subscription: {str(e)}")


# ===== MODEL MANAGEMENT ENDPOINTS =====

@router.post("/models/train/{commodity_slug}", response_model=ModelTrainingResponse)
async def train_commodity_model(
    commodity_slug: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Train ML model for a specific commodity
    
    Requires admin privileges or commodity owner access
    """
    try:
        # Check if commodity exists
        commodity = await listing_manager.get_by_slug(db, commodity_slug)
        if not commodity:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # For now, allow any authenticated user to train models
        # In production, you might want to restrict this to admins or commodity owners
        
        # Start training in background
        background_tasks.add_task(
            trainer.train_commodity_model,
            commodity_slug
        )
        
        return ModelTrainingResponse(
            success=True,
            message=f"Model training started for {commodity_slug}",
            training_time=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@router.post("/models/train-all", response_model=ModelTrainingResponse)
async def train_all_models(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Train ML models for all commodities with sufficient data
    
    Requires admin privileges
    """
    try:
        # Check if user is admin
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Start batch training in background
        background_tasks.add_task(trainer.train_all_models)
        
        return ModelTrainingResponse(
            success=True,
            message="Batch model training started for all commodities",
            training_time=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch training: {str(e)}")


@router.get("/models/status")
async def get_model_status(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of all ML models
    """
    try:
        status = model_manager.get_model_status()
        
        return {
            "models": status,
            "total_models": len(status),
            "trained_models": sum(1 for s in status.values() if s.get("is_trained")),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


# ===== ADMIN ENDPOINTS =====

@router.post("/admin/auto-bidding/process")
async def process_auto_bidding(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process all auto-bidding opportunities (Admin only)
    
    This endpoint is typically called by a scheduled task
    """
    try:
        # Check if user is admin
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        # Process auto-bidding in background
        background_tasks.add_task(auto_bidding_engine.process_auto_bidding_opportunities)
        
        return {"message": "Auto-bidding processing started"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process auto-bidding: {str(e)}")


@router.get("/health")
async def ml_health_check():
    """Health check for ML services"""
    try:
        model_status = model_manager.get_model_status()
        
        return {
            "status": "healthy",
            "ml_models_available": len(model_status),
            "trained_models": sum(1 for s in model_status.values() if s.get("is_trained")),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
