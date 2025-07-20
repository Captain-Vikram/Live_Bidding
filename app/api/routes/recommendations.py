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

try:
    from ml.prediction_models import model_manager
    from ml.trainers.model_trainer import trainer
    from ml.auto_bidding import auto_bidding_engine
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

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


@router.get("/trading-suggestion/{commodity_slug}", response_model=TradingSuggestionResponse)
async def get_trading_suggestion(
    commodity_slug: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ML-powered trading suggestion for a specific commodity
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML services are not available. Please install ML dependencies."
        )
    
    try:
        # Get commodity listing
        listing = await listing_manager.get_by_slug(db, commodity_slug)
        if not listing:
            raise HTTPException(status_code=404, detail="Commodity not found")
        
        # Get trading suggestion from ML model
        suggestion = await model_manager.get_trading_suggestion(db, commodity_slug)
        
        return suggestion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading suggestion: {str(e)}")


@router.get("/health")
async def ml_health_check():
    """Health check for ML services"""
    try:
        if not ML_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "ML services not installed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
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