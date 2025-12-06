"""
Incremental Training: Continue training from last checkpoint.

Features:
- Track last processed match ID
- Append new data to existing dataset
- Continue XGBoost training from checkpoint
- Avoid re-processing same matches
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger

import numpy as np

try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import log_loss, accuracy_score, roc_auc_score
    import joblib
except ImportError as e:
    logger.warning(f"ML dependencies not installed: {e}")
    xgb = None

from app.ml.versioning import version_manager, ModelMetadata
from app.ml.train import FEATURE_COLS, TARGET_COL


class IncrementalTrainer:
    """
    Supports incremental/continuous training.
    
    Modes:
    1. Fresh: Train from scratch on all data
    2. Append: Add new data to existing dataset, retrain
    3. Continue: Use XGBoost's warm start from previous model
    """
    
    DATA_DIR = Path("data/processed")
    SYNC_STATE_FILE = DATA_DIR / "sync_state.json"
    
    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._sync_state = self._load_sync_state()
    
    def _load_sync_state(self) -> Dict[str, Any]:
        """Load sync state (last match ID, etc.)."""
        if self.SYNC_STATE_FILE.exists():
            try:
                with open(self.SYNC_STATE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_match_id": None,
            "last_sync_time": None,
            "total_rows": 0,
        }
    
    def _save_sync_state(self):
        """Save sync state."""
        with open(self.SYNC_STATE_FILE, "w") as f:
            json.dump(self._sync_state, f, indent=2)
    
    @property
    def last_match_id(self) -> Optional[int]:
        """Get last synced match ID."""
        return self._sync_state.get("last_match_id")
    
    def update_sync_state(self, match_id: int, rows_added: int):
        """Update sync state after collecting new data."""
        self._sync_state["last_match_id"] = match_id
        self._sync_state["last_sync_time"] = datetime.utcnow().isoformat()
        self._sync_state["total_rows"] = self._sync_state.get("total_rows", 0) + rows_added
        self._save_sync_state()
    
    def append_training_data(self, new_rows: List[Dict]) -> int:
        """
        Append new training rows to existing dataset.
        
        Returns number of rows added (after dedup).
        """
        filepath = self.DATA_DIR / "training_data.jsonl"
        
        # Load existing match IDs to avoid duplicates
        existing_match_ids = set()
        if filepath.exists():
            with open(filepath, "r") as f:
                for line in f:
                    row = json.loads(line)
                    existing_match_ids.add(row.get("match_id"))
        
        # Filter new rows
        unique_rows = [r for r in new_rows if r.get("match_id") not in existing_match_ids]
        
        if not unique_rows:
            logger.info("No new unique rows to add")
            return 0
        
        # Append to file
        with open(filepath, "a") as f:
            for row in unique_rows:
                f.write(json.dumps(row) + "\n")
        
        logger.info(f"Appended {len(unique_rows)} new rows (filtered {len(new_rows) - len(unique_rows)} duplicates)")
        
        # Update last match ID
        max_match_id = max(r.get("match_id", 0) for r in unique_rows)
        self.update_sync_state(max_match_id, len(unique_rows))
        
        return len(unique_rows)
    
    def load_all_data(self, limit: int = 50000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load all training data.
        
        Args:
            limit: Max rows to load (rolling window for meta awareness).
                   Default 50,000 (~3 weeks of pro matches).
        """
        filepath = self.DATA_DIR / "training_data.jsonl"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Training data not found: {filepath}")
        
        rows = []
        with open(filepath, "r") as f:
            for line in f:
                rows.append(json.loads(line))
        
        # Rolling Window Strategy: Data closer to end is newer (by file append nature)
        if len(rows) > limit:
            logger.info(f"Applying Rolling Window: Keeping last {limit} of {len(rows)} rows")
            rows = rows[-limit:]
            
        logger.info(f"Loaded {len(rows)} features for training")
        
        X = np.array([[row.get(col, 0.0) for col in FEATURE_COLS] for row in rows])
        y = np.array([row.get(TARGET_COL, 0) for row in rows])
        
        return X, y
    
    def train_incremental(
        self,
        patch: str = "7.39e",
        test_size: float = 0.2,
        continue_from: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Train a new model version.
        
        Args:
            patch: Current Dota patch
            test_size: Fraction for test set
            continue_from: Version to continue from (warm start)
        
        Returns:
            Dict with version, paths, and metrics
        """
        if xgb is None:
            raise ImportError("XGBoost not installed")
        
        # Load data
        X, y = self.load_all_data()
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Training: {len(X_train)} samples, Test: {len(X_test)} samples")
        
        # Initialize model
        if continue_from and continue_from in version_manager._versions:
            # Warm start from previous model
            logger.info(f"Continuing from model v{continue_from}")
            model = version_manager.load_model(continue_from)
            
            # Additional boosting rounds
            model.set_params(n_estimators=model.n_estimators + 50)
            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                xgb_model=model.get_booster(),
                verbose=True
            )
            parent_version = continue_from
        else:
            # Fresh training
            logger.info("Training fresh model")
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
            parent_version = None
        
        # Evaluate
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
        
        metrics = {
            "logloss": float(log_loss(y_test, y_pred_proba)),
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "auc": float(roc_auc_score(y_test, y_pred_proba)),
        }
        
        # Isotonic calibration
        logger.info("Applying isotonic calibration...")
        calibrated = CalibratedClassifierCV(model, method="isotonic", cv="prefit")
        calibrated.fit(X_test, y_test)
        
        y_calibrated = calibrated.predict_proba(X_test)[:, 1]
        metrics["calibrated_logloss"] = float(log_loss(y_test, y_calibrated))
        
        # Get version number
        version = version_manager.get_next_version()
        
        # Save model files
        model_path = version_manager.MODEL_DIR / f"model_v{version}_patch{patch}.json"
        calib_path = version_manager.MODEL_DIR / f"calibration_v{version}_patch{patch}.pkl"
        
        model.save_model(model_path)
        joblib.dump(calibrated, calib_path)
        
        # Feature importance
        importance = dict(zip(FEATURE_COLS, [float(x) for x in model.feature_importances_]))
        
        # Register version
        metadata = version_manager.register_version(
            version=version,
            patch=patch,
            training_samples=len(X_train),
            test_samples=len(X_test),
            metrics=metrics,
            feature_importance=importance,
            last_match_id=self.last_match_id,
            parent_version=parent_version,
        )
        
        # Set as current
        version_manager.set_current(version)
        
        logger.info(f"✅ Trained model v{version}: {metrics}")
        
        return {
            "version": version,
            "patch": patch,
            "model_path": str(model_path),
            "calibration_path": str(calib_path),
            "metrics": metrics,
            "feature_importance": importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "parent_version": parent_version,
        }


# CLI entry point
def main():
    """Run incremental training from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental model training")
    parser.add_argument("--patch", type=str, default="7.39e", help="Dota patch version")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
    parser.add_argument("--continue-from", type=int, help="Version to continue from")
    args = parser.parse_args()
    
    trainer = IncrementalTrainer()
    result = trainer.train_incremental(
        patch=args.patch,
        test_size=args.test_size,
        continue_from=args.continue_from,
    )
    
    print("\n=== Incremental Training Complete ===")
    print(f"Version: v{result['version']}")
    print(f"Patch: {result['patch']}")
    print(f"Samples: {result['training_samples']} train, {result['test_samples']} test")
    print(f"Metrics: {result['metrics']}")


if __name__ == "__main__":
    main()
