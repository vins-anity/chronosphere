"""
Tests for Feature Extraction module.
"""
import pytest
from app.ml.features import FeatureExtractor, FeatureVector, FEATURE_NAMES


class TestFeatureVector:
    """Tests for FeatureVector dataclass."""
    
    def test_to_list_length(self):
        """Feature vector list should match FEATURE_NAMES length."""
        fv = FeatureVector()
        assert len(fv.to_list()) == len(FEATURE_NAMES)
    
    def test_to_list_order(self):
        """Feature values should be in correct order."""
        fv = FeatureVector(
            game_time=600,
            gold_diff=5000,
            xp_diff=2000,
        )
        values = fv.to_list()
        assert values[0] == 600  # game_time is first
        assert values[2] == 5000  # gold_diff is third
    
    def test_to_dict(self):
        """Feature dict should have correct keys."""
        fv = FeatureVector(game_time=300)
        d = fv.to_dict()
        assert "game_time" in d
        assert d["game_time"] == 300
    
    def test_default_values(self):
        """Default values should be zeros (except carry_efficiency)."""
        fv = FeatureVector()
        assert fv.game_time == 0.0
        assert fv.gold_diff == 0.0
        assert fv.carry_efficiency_index == 1.0  # Default is 1.0


class TestFeatureExtractor:
    """Tests for FeatureExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        return FeatureExtractor()
    
    def test_extract_empty_tick(self, extractor):
        """Empty tick should return safe defaults."""
        features = extractor.extract({})
        assert len(features) == len(FEATURE_NAMES)
        assert all(isinstance(f, (int, float)) for f in features)
    
    def test_extract_game_time(self, extractor):
        """Game time should be extracted from map data."""
        tick = {"map": {"clock_time": 600}}
        features = extractor.extract(tick)
        assert features[0] == 600  # game_time
        assert features[1] == pytest.approx(600 / 3600, rel=0.01)  # normalized
    
    def test_extract_gold_diff(self, extractor):
        """Gold difference should be calculated from team golds."""
        tick = {
            "map": {
                "radiant_gold": 30000,
                "dire_gold": 25000,
            }
        }
        features = extractor.extract(tick)
        assert features[2] == 5000  # gold_diff = 30000 - 25000
    
    def test_gold_diff_normalization(self, extractor):
        """Gold diff should be normalized to [-1, 1]."""
        tick = {"map": {"radiant_gold": 100000, "dire_gold": 0}}
        features = extractor.extract(tick)
        assert features[3] == 1.0  # Clamped to max
        
        tick = {"map": {"radiant_gold": 0, "dire_gold": 100000}}
        features = extractor.extract(tick)
        assert features[3] == -1.0  # Clamped to min
    
    def test_context_features(self, extractor):
        """Context features should be pulled from context dict."""
        tick = {}
        context = {
            "draft_score_diff": 0.15,
            "late_game_score_diff": -0.1,
            "series_score_diff": 1.0,
        }
        features = extractor.extract(tick, context)
        
        # Find index of draft_score_diff
        idx = FEATURE_NAMES.index("draft_score_diff")
        assert features[idx] == 0.15
    
    def test_gini_calculation_empty(self, extractor):
        """Gini with no players should return 0."""
        result = extractor._calculate_gini({})
        assert result == 0.0
    
    def test_gini_calculation(self, extractor):
        """Gini should be higher for unequal distributions."""
        # Equal distribution
        tick_equal = {
            "allplayers": {
                "0": {"net_worth": 10000, "team_slot": 0},
                "1": {"net_worth": 10000, "team_slot": 1},
                "2": {"net_worth": 10000, "team_slot": 2},
            }
        }
        gini_equal = extractor._calculate_gini(tick_equal)
        
        # Unequal distribution
        tick_unequal = {
            "allplayers": {
                "0": {"net_worth": 30000, "team_slot": 0},
                "1": {"net_worth": 5000, "team_slot": 1},
                "2": {"net_worth": 1000, "team_slot": 2},
            }
        }
        gini_unequal = extractor._calculate_gini(tick_unequal)
        
        assert gini_unequal > gini_equal
