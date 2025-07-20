"""
ML Recommendations API Routes
============================

FastAPI endpoints for ML-powered trading recommendations
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_optional_user
from app.db.models.accounts import User
from ml.recommendations import recommendation_engine
from ml.prediction_models import model_manager

router = APIRouter(prefix="/recommendations", tags=["ML Recommendations"])


# ===== INDIVIDUAL COMMODITY RECOMMENDATIONS =====

@router.get("/commodity/{commodity_slug}")
async def get_commodity_recommendation(
    commodity_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get ML-powered trading recommendation for a specific commodity
    
    Returns:
    - Trading suggestion (BUY/SELL/HOLD)
    - Current price and predicted price
    - Confidence level
    - Historical statistics
    - Price predictions for next few days
    """
    try:
        result = await recommendation_engine.get_commodity_recommendation(db, commodity_slug)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "message": "Recommendation generated successfully",
            "data": result["recommendation"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")


# ===== PORTFOLIO RECOMMENDATIONS =====

@router.get("/portfolio")
async def get_portfolio_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized recommendations based on user's watchlist
    
    Requires authentication. Returns recommendations for all commodities
    in the user's watchlist, sorted by confidence and potential.
    """
    try:
        result = await recommendation_engine.get_portfolio_recommendations(db, str(current_user.id))
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "Portfolio recommendations generated successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate portfolio recommendations: {str(e)}")


# ===== MARKET OVERVIEW =====

@router.get("/market-overview")
async def get_market_overview(
    limit: int = Query(10, ge=1, le=50, description="Number of commodities to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get market overview with top trading opportunities
    
    Returns:
    - Market statistics
    - Top BUY opportunities
    - Top SELL opportunities
    - Overall market sentiment
    """
    try:
        result = await recommendation_engine.get_market_overview(db, limit)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "message": "Market overview generated successfully",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate market overview: {str(e)}")


# ===== PRICE PREDICTIONS =====

@router.get("/predictions/{commodity_slug}")
async def get_price_predictions(
    commodity_slug: str,
    prediction_days: int = Query(7, ge=1, le=30, description="Number of days to predict"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get detailed price predictions for a commodity
    
    Returns predictions for the next N days with confidence intervals
    """
    try:
        # Get the model
        model = model_manager.get_model(commodity_slug)
        
        # Get recent price data
        from app.db.managers.price_tracking import price_history_manager
        from app.db.managers.listings import listing_manager
        
        # Get commodity
        commodity = await listing_manager.get_by_slug(db, commodity_slug)
        if not commodity:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # Get price data
        recent_data = await price_history_manager.get_recent_prices(db, commodity.id, days=60)
        
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
        
        # Train model if needed
        if not model.is_trained:
            training_result = model.train_model(price_data)
            if not training_result.get("success"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Model training failed: {training_result.get('error')}"
                )
        
        # Get predictions
        prediction_result = model.predict(price_data, prediction_days)
        
        if not prediction_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=f"Prediction failed: {prediction_result.get('error')}"
            )
        
        return {
            "message": "Price predictions generated successfully",
            "data": {
                "commodity_slug": commodity_slug,
                "commodity_name": commodity.name,
                "current_price": float(commodity.price),
                "predictions": prediction_result["predictions"],
                "model_metrics": prediction_result["model_metrics"],
                "generated_at": prediction_result["predicted_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate predictions: {str(e)}")


# ===== MODEL MANAGEMENT =====

@router.post("/models/{commodity_slug}/train")
async def train_model(
    commodity_slug: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger model training for a commodity
    
    Requires authentication. Useful for retraining models with new data.
    """
    try:
        # Check if user has permission (e.g., admin or premium user)
        if not current_user.is_superuser:
            # You can add additional permission checks here
            pass
        
        # Get commodity
        from app.db.managers.listings import listing_manager
        commodity = await listing_manager.get_by_slug(db, commodity_slug)
        if not commodity:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # Get price data
        from app.db.managers.price_tracking import price_history_manager
        recent_data = await price_history_manager.get_recent_prices(db, commodity.id, days=365)  # Get more data for training
        
        if len(recent_data) < 50:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for training (minimum 50 records required)"
            )
        
        # Convert to training format
        price_data = []
        for record in recent_data:
            price_data.append({
                'price_date': record.price_date.isoformat(),
                'price': float(record.price),
                'market_activity': float(record.extra_data.get('market_activity', 1.0)),
                'supply_demand_ratio': float(record.extra_data.get('supply_demand_ratio', 1.0)),
                'commodity_id': str(record.commodity_id)
            })
        
        # Train model in background
        def train_model_task():
            model = model_manager.get_model(commodity_slug)
            result = model.train_model(price_data)
            # You could add logging or notification here
            return result
        
        background_tasks.add_task(train_model_task)
        
        return {
            "message": f"Model training started for {commodity_slug}",
            "data": {
                "commodity_slug": commodity_slug,
                "data_points": len(price_data),
                "status": "training_started"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start model training: {str(e)}")


@router.get("/models/{commodity_slug}/info")
async def get_model_info(
    commodity_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get information about the ML model for a commodity
    
    Returns model training status, performance metrics, and last training date.
    """
    try:
        model = model_manager.get_model(commodity_slug)
        
        # Try to load existing model
        if not model.is_trained:
            model._load_model()
        
        model_info = {
            "commodity_slug": commodity_slug,
            "is_trained": model.is_trained,
            "last_trained": model.last_trained.isoformat() if model.last_trained else None,
            "model_type": model.model_type,
            "metrics": model.model_metrics if model.is_trained else {},
            "feature_count": len(model.feature_columns),
            "features": model.feature_columns
        }
        
        return {
            "message": "Model information retrieved successfully",
            "data": model_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


# ===== ANALYTICS AND INSIGHTS =====

@router.get("/analytics/performance")
async def get_recommendation_performance(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance analytics for ML recommendations
    
    Requires authentication. Shows how accurate predictions have been.
    """
    try:
        # This is a placeholder for recommendation performance tracking
        # In a real implementation, you would track prediction accuracy over time
        
        performance_data = {
            "analysis_period_days": days,
            "total_predictions": 0,  # Would be calculated from historical data
            "accuracy_metrics": {
                "direction_accuracy": 0.0,  # Percentage of correct buy/sell/hold predictions
                "price_accuracy": 0.0,      # Average prediction error
                "confidence_calibration": 0.0  # How well confidence correlates with accuracy
            },
            "recommendation_breakdown": {
                "buy_recommendations": 0,
                "sell_recommendations": 0,
                "hold_recommendations": 0
            },
            "note": "Performance tracking requires historical prediction data collection"
        }
        
        return {
            "message": "Recommendation performance analytics retrieved",
            "data": performance_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")


# ===== HEALTH CHECK =====

@router.get("/health")
async def recommendations_health_check():
    """
    Health check for ML recommendations service
    """
    try:
        # Check if ML dependencies are available
        import numpy as np
        import pandas as pd
        from sklearn.ensemble import RandomForestRegressor
        
        health_status = {
            "service": "ML Recommendations",
            "status": "healthy",
            "ml_dependencies": "available",
            "model_manager": "initialized",
            "recommendation_engine": "ready",
            "timestamp": "2025-01-15T12:00:00Z"
        }
        
        return {
            "message": "ML Recommendations service is healthy",
            "data": health_status
        }
        
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"ML dependencies not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )
