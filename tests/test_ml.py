"""
Tests for ML Pipeline: Training, Versioning, Incremental Training.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.ml.train import FEATURE_COLS, TARGET_COL
from app.core.rate_tracker import RateLimitTracker, APIQuota, UsageStats


class TestRateLimitTracker:
    """Tests for rate limit tracking."""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with temp data file."""
        tracker = RateLimitTracker()
        tracker.DATA_FILE = tmp_path / "rate_limits.json"
        tracker._usage = {}
        return tracker
    
    def test_can_call_under_limit(self, tracker):
        """Should allow calls when under limit."""
        assert tracker.can_call("opendota") is True
    
    def test_record_call_increments(self, tracker):
        """Recording a call should increment count."""
        tracker.record_call("opendota")
        assert tracker._usage["opendota"].total_calls == 1
        
        tracker.record_call("opendota")
        assert tracker._usage["opendota"].total_calls == 2
    
    def test_status_returns_all_apis(self, tracker):
        """Status should return info for all configured APIs."""
        status = tracker.status()
        assert "opendota" in status
        assert "pandascore" in status
        assert "stratz" in status
    
    def test_status_shows_usage(self, tracker):
        """Status should show current usage."""
        tracker.record_call("opendota")
        status = tracker.status()
        assert status["opendota"]["monthly_used"] == 1
    
    def test_block_at_limit(self, tracker):
        """Should block calls at 95% of limit."""
        # Simulate being at limit
        from app.core.rate_tracker import API_QUOTAS
        limit = API_QUOTAS["opendota"].monthly_limit
        tracker._usage["opendota"] = UsageStats(
            total_calls=int(limit * 0.96)  # Over 95%
        )
        assert tracker.can_call("opendota") is False


class TestFeatureCols:
    """Tests for feature column consistency."""
    
    def test_feature_cols_match_names(self):
        """FEATURE_COLS in train.py should match features.py FEATURE_NAMES."""
        from app.ml.features import FEATURE_NAMES
        assert FEATURE_COLS == FEATURE_NAMES
    
    def test_target_col_name(self):
        """Target column should be radiant_win."""
        assert TARGET_COL == "radiant_win"


class TestModelVersioning:
    """Tests for model version management."""
    
    @pytest.fixture
    def version_manager(self, tmp_path):
        """Create version manager with temp directory."""
        from app.ml.versioning import ModelVersionManager
        mgr = ModelVersionManager()
        mgr.MODEL_DIR = tmp_path / "models"
        mgr.MODEL_DIR.mkdir()
        mgr.METADATA_FILE = mgr.MODEL_DIR / "versions.json"
        mgr._versions = {}
        mgr._current_version = None
        return mgr
    
    def test_get_next_version_empty(self, version_manager):
        """Next version should be 1 when no versions exist."""
        assert version_manager.get_next_version() == 1
    
    def test_get_next_version_increments(self, version_manager):
        """Next version should increment from latest."""
        version_manager.register_version(
            version=1,
            patch="7.39e",
            training_samples=1000,
            test_samples=200,
            metrics={"logloss": 0.5},
            feature_importance={},
        )
        assert version_manager.get_next_version() == 2
    
    def test_register_version(self, version_manager):
        """Registering version should add to versions dict."""
        version_manager.register_version(
            version=1,
            patch="7.39e",
            training_samples=1000,
            test_samples=200,
            metrics={"logloss": 0.5},
            feature_importance={"gold_diff": 0.3},
        )
        assert 1 in version_manager._versions
        assert version_manager._versions[1].patch == "7.39e"
    
    def test_set_current(self, version_manager):
        """Setting current should update current_version."""
        version_manager.register_version(
            version=1,
            patch="7.39e",
            training_samples=1000,
            test_samples=200,
            metrics={},
            feature_importance={},
        )
        version_manager.set_current(1)
        assert version_manager.current_version == 1
    
    def test_list_versions(self, version_manager):
        """List versions should return metadata."""
        version_manager.register_version(
            version=1,
            patch="7.39e",
            training_samples=1000,
            test_samples=200,
            metrics={"logloss": 0.5},
            feature_importance={},
        )
        versions = version_manager.list_versions()
        assert len(versions) == 1
        assert versions[0]["version"] == 1
        assert versions[0]["patch"] == "7.39e"


class TestIncrementalTraining:
    """Tests for incremental training."""
    
    @pytest.fixture
    def trainer(self, tmp_path):
        """Create incremental trainer with temp data dir."""
        from app.ml.incremental import IncrementalTrainer
        trainer = IncrementalTrainer()
        trainer.DATA_DIR = tmp_path / "processed"
        trainer.DATA_DIR.mkdir()
        trainer.SYNC_STATE_FILE = tmp_path / "sync_state.json"
        trainer._sync_state = {"last_match_id": None, "total_rows": 0}
        return trainer
    
    def test_append_training_data_new(self, trainer):
        """Appending new data should add rows."""
        rows = [
            {"match_id": 1, "gold_diff": 1000, "radiant_win": 1},
            {"match_id": 2, "gold_diff": -500, "radiant_win": 0},
        ]
        added = trainer.append_training_data(rows)
        assert added == 2
    
    def test_append_training_data_dedup(self, trainer):
        """Duplicate match IDs should be filtered."""
        # Add initial data
        rows1 = [{"match_id": 1, "gold_diff": 1000, "radiant_win": 1}]
        trainer.append_training_data(rows1)
        
        # Try to add duplicate
        rows2 = [
            {"match_id": 1, "gold_diff": 1000, "radiant_win": 1},  # Duplicate
            {"match_id": 2, "gold_diff": -500, "radiant_win": 0},  # New
        ]
        added = trainer.append_training_data(rows2)
        assert added == 1  # Only the new one
    
    def test_update_sync_state(self, trainer):
        """Sync state should update after appending."""
        trainer.update_sync_state(match_id=12345, rows_added=50)
        assert trainer.last_match_id == 12345
        assert trainer._sync_state["total_rows"] == 50
