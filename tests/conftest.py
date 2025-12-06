"""
Pytest Configuration for Chronosphere tests.
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings for all tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("ALLOWED_IPS", '["*"]')
    monkeypatch.setenv("USE_MOCK_ODDS", "True")
    monkeypatch.setenv("USE_MOCK_CONTEXT", "True")


@pytest.fixture
def sample_gsi_tick():
    """Sample GSI tick data for testing."""
    return {
        "provider": {"timestamp": 1699999999},
        "map": {
            "clock_time": 1200,
            "radiant_gold": 45000,
            "dire_gold": 40000,
            "radiant_xp": 35000,
            "dire_xp": 32000,
        },
        "allplayers": {
            "0": {"net_worth": 12000, "team_slot": 0, "hero_id": 1},
            "1": {"net_worth": 10000, "team_slot": 1, "hero_id": 2},
            "2": {"net_worth": 8000, "team_slot": 2, "hero_id": 3},
            "3": {"net_worth": 7000, "team_slot": 3, "hero_id": 4},
            "4": {"net_worth": 5000, "team_slot": 4, "hero_id": 5},
            "5": {"net_worth": 11000, "team_slot": 5, "hero_id": 6},
            "6": {"net_worth": 9000, "team_slot": 6, "hero_id": 7},
            "7": {"net_worth": 8500, "team_slot": 7, "hero_id": 8},
            "8": {"net_worth": 6500, "team_slot": 8, "hero_id": 9},
            "9": {"net_worth": 5000, "team_slot": 9, "hero_id": 10},
        }
    }


@pytest.fixture
def sample_training_row():
    """Sample training data row."""
    return {
        "match_id": 7654321,
        "game_time": 1800,
        "game_time_normalized": 0.5,
        "gold_diff": 5000,
        "gold_diff_normalized": 0.1,
        "xp_diff": 3000,
        "xp_diff_normalized": 0.1,
        "networth_velocity": 50.0,
        "networth_gini": 0.3,
        "buyback_power_ratio": 0.0,
        "draft_score_diff": 0.05,
        "late_game_score_diff": -0.1,
        "series_score_diff": 0.0,
        "carry_efficiency_index": 1.1,
        "radiant_win": 1,
    }
