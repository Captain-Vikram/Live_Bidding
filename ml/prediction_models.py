"""
Price Prediction Models
======================

Machine learning models for commodity price prediction and trading recommendations
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

# Model storage paths
ML_MODELS_DIR = Path(__file__).parent / "models"
ML_MODELS_DIR.mkdir(exist_ok=True)


class PricePredictionModel:
    """
    Advanced price prediction model using ensemble methods
    """
    
    def __init__(self, commodity_slug: str):
        self.commodity_slug = commodity_slug
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_importance = {}
        self.model_metrics = {}
        self.is_trained = False
        
        # Model file paths
        self.model_path = ML_MODELS_DIR / f"{commodity_slug}_price_model.pkl"
        self.scaler_path = ML_MODELS_DIR / f"{commodity_slug}_scaler.pkl"
        self.metrics_path = ML_MODELS_DIR / f"{commodity_slug}_metrics.pkl"
        
    def _create_features(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features for price prediction
        """
        df = price_data.copy()
        df['price_date'] = pd.to_datetime(df['price_date'])
        df = df.sort_values('price_date')
        
        # Technical indicators
        df['price_ma_7'] = df['price'].rolling(window=7, min_periods=1).mean()
        df['price_ma_14'] = df['price'].rolling(window=14, min_periods=1).mean()
        df['price_ma_30'] = df['price'].rolling(window=30, min_periods=1).mean()
        
        # Price volatility
        df['price_std_7'] = df['price'].rolling(window=7, min_periods=1).std().fillna(0)
        df['price_std_14'] = df['price'].rolling(window=14, min_periods=1).std().fillna(0)
        
        # Price momentum
        df['price_change_1d'] = df['price'].pct_change(1).fillna(0)
        df['price_change_7d'] = df['price'].pct_change(7).fillna(0)
        df['price_change_14d'] = df['price'].pct_change(14).fillna(0)
        
        # Price position relative to moving averages
        df['price_vs_ma7'] = (df['price'] - df['price_ma_7']) / df['price_ma_7']
        df['price_vs_ma14'] = (df['price'] - df['price_ma_14']) / df['price_ma_14']
        df['price_vs_ma30'] = (df['price'] - df['price_ma_30']) / df['price_ma_30']
        
        # Time-based features
        df['day_of_week'] = df['price_date'].dt.dayofweek
        df['day_of_month'] = df['price_date'].dt.day
        df['month'] = df['price_date'].dt.month
        df['quarter'] = df['price_date'].dt.quarter
        
        # Market activity features
        df['market_activity'] = df.get('market_activity', 1.0)  # Default if not available
        df['supply_demand_ratio'] = df.get('supply_demand_ratio', 1.0)  # Default if not available
        
        # Lag features
        for lag in [1, 2, 3, 7, 14]:
            df[f'price_lag_{lag}'] = df['price'].shift(lag)
        
        # Fill any remaining NaN values
        df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
        
        return df
    
    def train(self, price_data: List[Dict]) -> Dict:
        """
        Train the price prediction model
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(price_data)
            
            if len(df) < 30:  # Need minimum data for meaningful training
                logger.warning(f"Insufficient data for {self.commodity_slug}: {len(df)} records")
                return {"error": "Insufficient training data", "min_required": 30}
            
            # Create features
            df = self._create_features(df)
            
            # Prepare features and target
            feature_columns = [
                'price_ma_7', 'price_ma_14', 'price_ma_30',
                'price_std_7', 'price_std_14',
                'price_change_1d', 'price_change_7d', 'price_change_14d',
                'price_vs_ma7', 'price_vs_ma14', 'price_vs_ma30',
                'day_of_week', 'day_of_month', 'month', 'quarter',
                'market_activity', 'supply_demand_ratio'
            ]
            
            # Add lag features
            for lag in [1, 2, 3, 7, 14]:
                feature_columns.append(f'price_lag_{lag}')
            
            X = df[feature_columns].values
            y = df['price'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Train ensemble model
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'linear_regression': LinearRegression()
            }
            
            best_model = None
            best_score = float('-inf')
            model_scores = {}
            
            for name, model in models.items():
                # Cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='r2')
                avg_score = cv_scores.mean()
                model_scores[name] = avg_score
                
                logger.info(f"{name} CV Score: {avg_score:.4f}")
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_model = model
            
            # Train best model on full training data
            best_model.fit(X_train, y_train)
            self.model = best_model
            
            # Calculate metrics
            y_pred = best_model.predict(X_test)
            
            self.model_metrics = {
                'mae': mean_absolute_error(y_test, y_pred),
                'mse': mean_squared_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred),
                'cv_scores': model_scores,
                'best_model': type(best_model).__name__,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'feature_count': len(feature_columns)
            }
            
            # Feature importance (if available)
            if hasattr(best_model, 'feature_importances_'):
                self.feature_importance = dict(zip(feature_columns, best_model.feature_importances_))
            
            self.is_trained = True
            
            # Save model artifacts
            self._save_model()
            
            logger.info(f"Model trained successfully for {self.commodity_slug}")
            logger.info(f"R² Score: {self.model_metrics['r2']:.4f}")
            logger.info(f"RMSE: {self.model_metrics['rmse']:.4f}")
            
            return {
                "success": True,
                "metrics": self.model_metrics,
                "feature_importance": self.feature_importance
            }
            
        except Exception as e:
            logger.error(f"Training failed for {self.commodity_slug}: {str(e)}")
            return {"error": str(e)}
    
    def predict(self, recent_data: List[Dict], prediction_days: int = 7) -> Dict:
        """
        Make price predictions for the next N days
        """
        try:
            if not self.is_trained and not self._load_model():
                return {"error": "Model not trained"}
            
            # Convert to DataFrame
            df = pd.DataFrame(recent_data)
            df = self._create_features(df)
            
            # Get the most recent record for prediction
            latest_record = df.iloc[-1:].copy()
            
            predictions = []
            current_record = latest_record.copy()
            
            for day in range(1, prediction_days + 1):
                # Prepare features
                feature_columns = [
                    'price_ma_7', 'price_ma_14', 'price_ma_30',
                    'price_std_7', 'price_std_14',
                    'price_change_1d', 'price_change_7d', 'price_change_14d',
                    'price_vs_ma7', 'price_vs_ma14', 'price_vs_ma30',
                    'day_of_week', 'day_of_month', 'month', 'quarter',
                    'market_activity', 'supply_demand_ratio'
                ]
                
                # Add lag features
                for lag in [1, 2, 3, 7, 14]:
                    feature_columns.append(f'price_lag_{lag}')
                
                X = current_record[feature_columns].values
                X_scaled = self.scaler.transform(X)
                
                # Make prediction
                predicted_price = self.model.predict(X_scaled)[0]
                
                # Calculate prediction date
                last_date = pd.to_datetime(current_record['price_date'].iloc[0])
                prediction_date = last_date + timedelta(days=day)
                
                predictions.append({
                    'date': prediction_date.isoformat(),
                    'predicted_price': round(float(predicted_price), 2),
                    'day_ahead': day
                })
                
                # Update current record for next iteration (simplified)
                current_record.loc[current_record.index[0], 'price'] = predicted_price
                current_record = self._create_features(current_record)
            
            return {
                "success": True,
                "predictions": predictions,
                "model_confidence": self.model_metrics.get('r2', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Prediction failed for {self.commodity_slug}: {str(e)}")
            return {"error": str(e)}
    
    def get_trading_suggestion(self, current_price: float, predicted_price: float, 
                             historical_stats: Dict) -> Dict:
        """
        Generate trading suggestions based on predictions and market analysis
        """
        try:
            avg_price_30d = historical_stats.get('avg_price_30d', current_price)
            price_volatility = historical_stats.get('volatility', 0.1)
            
            # Calculate price signals
            price_change_pct = ((predicted_price - current_price) / current_price) * 100
            price_vs_avg_pct = ((current_price - avg_price_30d) / avg_price_30d) * 100
            
            # Determine suggestion based on multiple factors
            confidence = self.model_metrics.get('r2', 0.0)
            
            # Trading logic
            if price_change_pct > 5 and current_price < avg_price_30d * 1.1:
                suggestion = "BUY"
                reason = "Price expected to rise significantly and currently below average"
            elif price_change_pct < -5 and current_price > avg_price_30d * 0.9:
                suggestion = "SELL"
                reason = "Price expected to fall significantly and currently above average"
            elif abs(price_change_pct) < 2:
                suggestion = "HOLD"
                reason = "Price expected to remain stable"
            elif price_vs_avg_pct > 15:
                suggestion = "SELL"
                reason = "Current price significantly above historical average"
            elif price_vs_avg_pct < -15:
                suggestion = "BUY"
                reason = "Current price significantly below historical average"
            else:
                suggestion = "HOLD"
                reason = "Mixed signals, recommend waiting for clearer trend"
            
            # Adjust confidence based on volatility
            volatility_factor = max(0.5, 1 - price_volatility)
            adjusted_confidence = confidence * volatility_factor
            
            return {
                "suggestion": suggestion,
                "current_price": round(current_price, 2),
                "predicted_price": round(predicted_price, 2),
                "avg_price_30d": round(avg_price_30d, 2),
                "confidence": round(adjusted_confidence, 3),
                "price_change_pct": round(price_change_pct, 2),
                "reason": reason,
                "volatility": round(price_volatility, 3),
                "market_position": "ABOVE_AVG" if price_vs_avg_pct > 0 else "BELOW_AVG"
            }
            
        except Exception as e:
            logger.error(f"Trading suggestion failed: {str(e)}")
            return {"error": str(e)}
    
    def _save_model(self):
        """Save model artifacts to disk"""
        try:
            # Save model
            joblib.dump(self.model, self.model_path)
            
            # Save scaler
            joblib.dump(self.scaler, self.scaler_path)
            
            # Save metrics
            with open(self.metrics_path, 'wb') as f:
                pickle.dump(self.model_metrics, f)
                
            logger.info(f"Model artifacts saved for {self.commodity_slug}")
            
        except Exception as e:
            logger.error(f"Failed to save model for {self.commodity_slug}: {str(e)}")
    
    def _load_model(self) -> bool:
        """Load model artifacts from disk"""
        try:
            if not all([self.model_path.exists(), self.scaler_path.exists(), self.metrics_path.exists()]):
                return False
            
            # Load model
            self.model = joblib.load(self.model_path)
            
            # Load scaler
            self.scaler = joblib.load(self.scaler_path)
            
            # Load metrics
            with open(self.metrics_path, 'rb') as f:
                self.model_metrics = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Model artifacts loaded for {self.commodity_slug}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model for {self.commodity_slug}: {str(e)}")
            return False


class ModelManager:
    """
    Manages multiple commodity prediction models
    """
    
    def __init__(self):
        self.models = {}
    
    def get_model(self, commodity_slug: str) -> PricePredictionModel:
        """Get or create a model for a commodity"""
        if commodity_slug not in self.models:
            self.models[commodity_slug] = PricePredictionModel(commodity_slug)
        return self.models[commodity_slug]
    
    def train_all_models(self, commodity_data: Dict[str, List[Dict]]) -> Dict:
        """Train models for all commodities"""
        results = {}
        
        for commodity_slug, price_data in commodity_data.items():
            model = self.get_model(commodity_slug)
            result = model.train(price_data)
            results[commodity_slug] = result
            
        return results
    
    def get_model_status(self) -> Dict:
        """Get status of all models"""
        status = {}
        
        for commodity_slug, model in self.models.items():
            status[commodity_slug] = {
                "is_trained": model.is_trained,
                "metrics": model.model_metrics,
                "model_file_exists": model.model_path.exists()
            }
        
        return status


# Alias for backward compatibility and clearer naming
CommodityPredictionModel = PricePredictionModel

# Global model manager instance
model_manager = ModelManager()
