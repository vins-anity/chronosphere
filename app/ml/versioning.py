"""
Model Versioning System: Track, load, and manage ML model versions.

Features:
- Semantic versioning (v1, v2, etc.)
- Patch-aware naming
- Metadata tracking (training date, samples, metrics)
- Hot-swap capability
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger

try:
    import xgboost as xgb
    import joblib
except ImportError:
    xgb = None
    joblib = None


@dataclass
class ModelMetadata:
    """Metadata for a trained model."""
    version: int
    patch: str
    created_at: str
    training_samples: int
    test_samples: int
    metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    last_match_id: Optional[int] = None  # For incremental training
    parent_version: Optional[int] = None  # If trained incrementally


class ModelVersionManager:
    """
    Manages model versions with metadata.
    
    Naming convention:
    - Model: model_v{N}_patch{PATCH}.json
    - Calibration: calibration_v{N}_patch{PATCH}.pkl
    - Metadata: metadata_v{N}.json
    """
    
    MODEL_DIR = Path("app/ml/models")
    METADATA_FILE = MODEL_DIR / "versions.json"
    
    def __init__(self):
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self._versions: Dict[int, ModelMetadata] = {}
        self._current_version: Optional[int] = None
        self._load_metadata()
    
    def _load_metadata(self):
        """Load version metadata from file."""
        if self.METADATA_FILE.exists():
            try:
                with open(self.METADATA_FILE, "r") as f:
                    data = json.load(f)
                    self._current_version = data.get("current_version")
                    for v, meta in data.get("versions", {}).items():
                        self._versions[int(v)] = ModelMetadata(**meta)
            except Exception as e:
                logger.warning(f"Failed to load version metadata: {e}")
    
    def _save_metadata(self):
        """Save version metadata to file."""
        data = {
            "current_version": self._current_version,
            "versions": {str(v): asdict(m) for v, m in self._versions.items()}
        }
        with open(self.METADATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    @property
    def current_version(self) -> Optional[int]:
        """Get current active version."""
        return self._current_version
    
    @property
    def latest_version(self) -> Optional[int]:
        """Get highest version number."""
        return max(self._versions.keys()) if self._versions else None
    
    def get_next_version(self) -> int:
        """Get next version number."""
        return (self.latest_version or 0) + 1
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """List all available versions with metadata."""
        result = []
        for v, meta in sorted(self._versions.items()):
            result.append({
                "version": v,
                "patch": meta.patch,
                "created_at": meta.created_at,
                "samples": meta.training_samples,
                "metrics": meta.metrics,
                "is_current": v == self._current_version,
            })
        return result
    
    def register_version(
        self,
        version: int,
        patch: str,
        training_samples: int,
        test_samples: int,
        metrics: Dict[str, float],
        feature_importance: Dict[str, float],
        last_match_id: Optional[int] = None,
        parent_version: Optional[int] = None,
    ) -> ModelMetadata:
        """Register a new model version."""
        metadata = ModelMetadata(
            version=version,
            patch=patch,
            created_at=datetime.utcnow().isoformat(),
            training_samples=training_samples,
            test_samples=test_samples,
            metrics=metrics,
            feature_importance=feature_importance,
            last_match_id=last_match_id,
            parent_version=parent_version,
        )
        
        self._versions[version] = metadata
        self._save_metadata()
        
        logger.info(f"📦 Registered model v{version} (patch {patch})")
        return metadata
    
    def set_current(self, version: int) -> bool:
        """Set the current active version."""
        if version not in self._versions:
            logger.error(f"Version {version} not found")
            return False
        
        self._current_version = version
        self._save_metadata()
        
        # Also update symlink/copy to model_latest.json
        self._update_latest_symlink(version)
        
        logger.info(f"✅ Set current model to v{version}")
        return True
    
    def _update_latest_symlink(self, version: int):
        """Update model_latest.json to point to specified version."""
        meta = self._versions[version]
        
        # Source files
        model_src = self.MODEL_DIR / f"model_v{version}_patch{meta.patch}.json"
        calib_src = self.MODEL_DIR / f"calibration_v{version}_patch{meta.patch}.pkl"
        
        # Target files
        model_dst = self.MODEL_DIR / "model_latest.json"
        calib_dst = self.MODEL_DIR / "calibration_model.pkl"
        
        # Copy (Windows doesn't support symlinks well)
        if model_src.exists():
            import shutil
            shutil.copy(model_src, model_dst)
        
        if calib_src.exists():
            import shutil
            shutil.copy(calib_src, calib_dst)
    
    def get_model_path(self, version: Optional[int] = None) -> Path:
        """Get path to model file for a version."""
        v = version or self._current_version or self.latest_version
        if v is None:
            return self.MODEL_DIR / "model_latest.json"
        
        meta = self._versions.get(v)
        if meta:
            return self.MODEL_DIR / f"model_v{v}_patch{meta.patch}.json"
        
        return self.MODEL_DIR / "model_latest.json"
    
    def get_calibration_path(self, version: Optional[int] = None) -> Path:
        """Get path to calibration model for a version."""
        v = version or self._current_version or self.latest_version
        if v is None:
            return self.MODEL_DIR / "calibration_model.pkl"
        
        meta = self._versions.get(v)
        if meta:
            return self.MODEL_DIR / f"calibration_v{v}_patch{meta.patch}.pkl"
        
        return self.MODEL_DIR / "calibration_model.pkl"
    
    def load_model(self, version: Optional[int] = None):
        """Load XGBoost model for a version."""
        if xgb is None:
            raise ImportError("XGBoost not installed")
        
        path = self.get_model_path(version)
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        
        model = xgb.XGBClassifier()
        model.load_model(path)
        return model
    
    def load_calibrator(self, version: Optional[int] = None):
        """Load calibration model for a version."""
        if joblib is None:
            raise ImportError("joblib not installed")
        
        path = self.get_calibration_path(version)
        if not path.exists():
            return None
        
        return joblib.load(path)
    
    def get_last_match_id(self, version: Optional[int] = None) -> Optional[int]:
        """Get last match ID used for training (for incremental)."""
        v = version or self.latest_version
        if v and v in self._versions:
            return self._versions[v].last_match_id
        return None
    
    def delete_version(self, version: int) -> bool:
        """Delete a model version and its files."""
        if version not in self._versions:
            return False
        
        meta = self._versions[version]
        
        # Delete files
        model_path = self.MODEL_DIR / f"model_v{version}_patch{meta.patch}.json"
        calib_path = self.MODEL_DIR / f"calibration_v{version}_patch{meta.patch}.pkl"
        
        if model_path.exists():
            model_path.unlink()
        if calib_path.exists():
            calib_path.unlink()
        
        # Remove from registry
        del self._versions[version]
        
        # Update current if needed
        if self._current_version == version:
            self._current_version = self.latest_version
        
        self._save_metadata()
        logger.info(f"🗑️ Deleted model v{version}")
        return True


# Singleton instance
version_manager = ModelVersionManager()
