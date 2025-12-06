"""
Training Pipeline: Trains XGBoost model with Isotonic Calibration.

Implements:
- Data loading from collected JSONL
- XGBoost training with logloss metric
- Isotonic calibration for probability accuracy
- Model versioning and saving
"""
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any
from datetime import datetime
from loguru import logger

import numpy as np

# ML imports (lazy loaded to reduce startup time)
try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import log_loss, accuracy_score, roc_auc_score
    import joblib
except ImportError as e:
    logger.warning(f"ML dependencies not installed: {e}")
    xgb = None


# Feature columns (must match features.py FEATURE_NAMES)
FEATURE_COLS = [
    "game_time",
    "game_time_normalized",
    "gold_diff",
    "gold_diff_normalized",
    "xp_diff",
    "xp_diff_normalized",
    "networth_velocity",
    "networth_gini",
    "buyback_power_ratio",
    "draft_score_diff",
    "late_game_score_diff",
    "series_score_diff",
    "carry_efficiency_index",
]

TARGET_COL = "radiant_win"


class ModelTrainer:
    """Trains and calibrates XGBoost model."""
    
    DATA_DIR = Path("data/processed")
    MODEL_DIR = Path("app/ml/models")
    
    def __init__(self):
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_data(self, filepath: Path = None) -> Tuple[np.ndarray, np.ndarray]:
        """Load training data from JSONL file."""
        filepath = filepath or self.DATA_DIR / "training_data.jsonl"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Training data not found: {filepath}")
        
        rows = []
        with open(filepath, "r") as f:
            for line in f:
                rows.append(json.loads(line))
        
        logger.info(f"Loaded {len(rows)} training rows")
        
        # Extract features and target
        X = np.array([[row.get(col, 0.0) for col in FEATURE_COLS] for row in rows])
        y = np.array([row.get(TARGET_COL, 0) for row in rows])
        
        return X, y
    
    def train(self, test_size: float = 0.2, calibrate: bool = True) -> Dict[str, Any]:
        """
        Train XGBoost model.
        
        Args:
            test_size: Fraction of data for testing
            calibrate: Whether to apply isotonic calibration
        
        Returns:
            Dict with model path and metrics
        """
        if xgb is None:
            raise ImportError("XGBoost not installed. Run: uv add xgboost scikit-learn")
        
        # Load data
        X, y = self.load_data()
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Training set: {len(X_train)}, Test set: {len(X_test)}")
        
        # Train XGBoost
        logger.info("Training XGBoost model...")
        
        model = xgb.XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=True)
        
        # Evaluate raw model
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
        
        metrics = {
            "raw_logloss": log_loss(y_test, y_pred_proba),
            "raw_accuracy": accuracy_score(y_test, y_pred),
            "raw_auc": roc_auc_score(y_test, y_pred_proba),
        }
        
        logger.info(f"Raw model metrics: {metrics}")
        
        # Calibrate
        if calibrate:
            logger.info("Applying isotonic calibration...")
            calibrated_model = CalibratedClassifierCV(
                model, method="isotonic", cv="prefit"
            )
            calibrated_model.fit(X_test, y_test)
            
            y_calibrated_proba = calibrated_model.predict_proba(X_test)[:, 1]
            
            metrics["calibrated_logloss"] = log_loss(y_test, y_calibrated_proba)
            logger.info(f"Calibrated logloss: {metrics['calibrated_logloss']}")
            
            # Save calibrated model
            calibration_path = self.MODEL_DIR / "calibration_model.pkl"
            joblib.dump(calibrated_model, calibration_path)
            logger.info(f"Saved calibration model to {calibration_path}")
        
        # Save XGBoost model
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_path = self.MODEL_DIR / f"model_{timestamp}.json"
        model.save_model(model_path)
        
        # Also save as latest
        latest_path = self.MODEL_DIR / "model_latest.json"
        model.save_model(latest_path)
        
        logger.info(f"Saved model to {model_path}")
        
        # Save feature importance
        importance = dict(zip(FEATURE_COLS, model.feature_importances_))
        logger.info(f"Feature importance: {importance}")
        
        return {
            "model_path": str(model_path),
            "metrics": metrics,
            "feature_importance": importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }


# CLI entry point
def main():
    """Run training from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train XGBoost model")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
    parser.add_argument("--no-calibrate", action="store_true", help="Skip calibration")
    args = parser.parse_args()
    
    trainer = ModelTrainer()
    result = trainer.train(test_size=args.test_size, calibrate=not args.no_calibrate)
    
    print("\n=== Training Complete ===")
    print(f"Model: {result['model_path']}")
    print(f"Metrics: {result['metrics']}")


if __name__ == "__main__":
    main()
