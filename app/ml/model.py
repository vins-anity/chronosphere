"""
Model Wrapper: Loads and runs XGBoost inference with optional calibration.

Implements:
- Model loading from JSON (XGBoost native format)
- Calibration model loading (scikit-learn joblib)
- Fallback heuristic when no model is trained
- Feature importance access
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger
import math
import numpy as np

# Lazy imports for ML libraries
try:
    import xgboost as xgb
    import joblib
    HAS_ML = True
except ImportError:
    HAS_ML = False
    xgb = None
    joblib = None


class ModelWrapper:
    """
    Wrapper for XGBoost model with optional isotonic calibration.
    
    Falls back to heuristic if no trained model is available.
    """
    
    MODEL_DIR = Path("app/ml/models")
    
    def __init__(self, model_path: Optional[str] = None, calibration_path: Optional[str] = None):
        self.model = None
        self.calibrator = None
        self._feature_importance: Dict[str, float] = {}
        
        # Try to load latest model if no path specified
        if model_path is None:
            model_path = self.MODEL_DIR / "model_latest.json"
        if calibration_path is None:
            calibration_path = self.MODEL_DIR / "calibration_model.pkl"
        
        self.load_model(model_path)
        self.load_calibrator(calibration_path)
    
    def load_model(self, path: str | Path):
        """Load XGBoost model from file."""
        if not HAS_ML:
            logger.warning("XGBoost not installed, using heuristic fallback")
            return
        
        path = Path(path)
        if not path.exists():
            logger.warning(f"Model file not found: {path}, using heuristic fallback")
            return
        
        try:
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(path))
            
            # Extract feature importance
            if hasattr(self.model, 'feature_importances_'):
                from app.ml.features import FEATURE_NAMES
                self._feature_importance = dict(zip(FEATURE_NAMES, self.model.feature_importances_))
            
            logger.info(f"Loaded XGBoost model from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def load_calibrator(self, path: str | Path):
        """Load isotonic calibration model."""
        if not HAS_ML or joblib is None:
            return
        
        path = Path(path)
        if not path.exists():
            logger.debug(f"Calibration model not found: {path}")
            return
        
        try:
            self.calibrator = joblib.load(path)
            logger.info(f"Loaded calibration model from {path}")
        except Exception as e:
            logger.error(f"Failed to load calibrator: {e}")
            self.calibrator = None
    
    def predict(self, features: List[float]) -> float:
        """
        Predict Radiant win probability.
        
        Args:
            features: Feature vector from FeatureExtractor
        
        Returns:
            Probability between 0.0 and 1.0
        """
        # Use trained model if available
        if self.model is not None and HAS_ML:
            try:
                X = np.array([features])
                
                if self.calibrator is not None:
                    # Use calibrated predictions
                    prob = self.calibrator.predict_proba(X)[0, 1]
                else:
                    # Use raw model predictions
                    prob = self.model.predict_proba(X)[0, 1]
                
                return float(prob)
                
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                # Fall through to heuristic
        
        # Fallback: Heuristic based on features
        return self._heuristic_predict(features)
    
    def _heuristic_predict(self, features: List[float]) -> float:
        """
        Fallback heuristic when no trained model is available.
        
        Uses a simple logistic function based on gold_diff and game_time.
        """
        # Expected feature order (see features.py):
        # 0: game_time
        # 1: game_time_normalized
        # 2: gold_diff
        # 3: gold_diff_normalized
        # 4: xp_diff
        # 5: xp_diff_normalized
        # ...
        
        game_time = features[0] if len(features) > 0 else 0
        gold_diff = features[2] if len(features) > 2 else 0
        gold_diff_normalized = features[3] if len(features) > 3 else 0
        xp_diff_normalized = features[5] if len(features) > 5 else 0
        velocity = features[6] if len(features) > 6 else 0
        
        # Base probability from normalized gold diff
        # Using logistic function: 1 / (1 + exp(-k * x))
        # k controls steepness; gold_diff_normalized is in [-1, 1]
        k = 3.0  # Steepness factor
        
        # Combine gold and XP with weights
        combined = gold_diff_normalized * 0.6 + xp_diff_normalized * 0.4
        
        # Add velocity influence (momentum matters)
        velocity_factor = velocity / 100.0  # Normalize velocity
        combined += velocity_factor * 0.2
        
        # Apply logistic transformation
        base_prob = 1.0 / (1.0 + math.exp(-k * combined))
        
        # Time factor: Early game differences matter less
        time_weight = min(1.0, game_time / 1200.0)  # Ramp up over 20 minutes
        
        # Final probability: blend with 50% base weighted by time
        prob = 0.5 + (base_prob - 0.5) * time_weight
        
        # Clamp to valid range
        return max(0.01, min(0.99, prob))
    
    def predict_batch(self, features_batch: List[List[float]]) -> List[float]:
        """Predict for multiple feature vectors."""
        return [self.predict(f) for f in features_batch]
    
    @property
    def feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        return self._feature_importance
    
    @property
    def is_trained(self) -> bool:
        """Check if a trained model is loaded."""
        return self.model is not None
    
    @property
    def is_calibrated(self) -> bool:
        """Check if calibration is applied."""
        return self.calibrator is not None


# Singleton for reuse in worker
model_wrapper = ModelWrapper()
