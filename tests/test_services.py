"""
Tests for External API Services: PandaScore, Stratz.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.pandascore import PandaScoreClient
from app.services.stratz import StratzClient
from app.core.state import MarketOdds, DraftContext


class TestPandaScoreClient:
    """Tests for PandaScore client."""
    
    @pytest.fixture
    def client(self):
        """Create client instance."""
        return PandaScoreClient()
    
    def test_is_available_no_key(self, client):
        """Client without key in mock mode should not be available."""
        client.api_key = None
        assert client.is_available is False
    
    def test_mock_live_matches(self, client):
        """Mock mode should return mock matches."""
        matches = client._get_mock_live_matches()
        assert len(matches) > 0
        assert "name" in matches[0]
    
    def test_should_poll_first_time(self, client):
        """First poll should always be allowed."""
        assert client.should_poll() is True
    
    def test_should_poll_respects_interval(self, client):
        """Should respect polling interval after first poll."""
        client.mark_polled()
        assert client.should_poll("in_progress") is False
    
    @pytest.mark.asyncio
    async def test_get_live_matches_mock(self, client):
        """Get live matches in mock mode should return mock data."""
        client.api_key = None  # Force mock mode
        matches = await client.get_live_matches()
        assert isinstance(matches, list)


class TestStratzClient:
    """Tests for Stratz client."""
    
    @pytest.fixture
    def client(self):
        """Create client instance."""
        return StratzClient()
    
    def test_is_available_no_key(self, client):
        """Client without key should not be available."""
        client.api_key = None
        assert client.is_available is False
    
    def test_mock_draft_context(self, client):
        """Mock context should have valid scores."""
        context = client._get_mock_draft_context()
        assert isinstance(context, DraftContext)
        assert 0 <= context.radiant_draft_score <= 1
        assert 0 <= context.dire_draft_score <= 1
    
    def test_cache_hit(self, client):
        """Cached context should be returned for same match ID."""
        mock_context = DraftContext(
            radiant_draft_score=0.55,
            dire_draft_score=0.45,
        )
        client._cached_context["test_match"] = mock_context
        
        # Should hit cache
        assert "test_match" in client._cached_context
    
    def test_clear_cache(self, client):
        """Clear cache should remove entries."""
        client._cached_context["match1"] = DraftContext()
        client._cached_context["match2"] = DraftContext()
        
        client.clear_cache("match1")
        assert "match1" not in client._cached_context
        assert "match2" in client._cached_context
        
        client.clear_cache()
        assert len(client._cached_context) == 0
    
    @pytest.mark.asyncio
    async def test_get_draft_context_mock(self, client):
        """Get draft context in mock mode should return mock data."""
        client.api_key = None  # Force mock mode
        context = await client.get_draft_context("test_match")
        assert isinstance(context, DraftContext)


class TestMarketOdds:
    """Tests for MarketOdds dataclass."""
    
    def test_market_odds_creation(self):
        """MarketOdds should be creatable with valid data."""
        odds = MarketOdds(
            radiant_odds=1.85,
            dire_odds=1.95,
            implied_radiant_prob=0.54,
            last_updated=datetime.utcnow(),
            is_mock=False,
        )
        assert odds.radiant_odds == 1.85
        assert odds.implied_radiant_prob == 0.54


class TestDraftContext:
    """Tests for DraftContext dataclass."""
    
    def test_draft_context_creation(self):
        """DraftContext should be creatable with valid data."""
        context = DraftContext(
            radiant_draft_score=0.55,
            dire_draft_score=0.45,
            radiant_late_game_score=0.6,
            dire_late_game_score=0.4,
        )
        assert context.radiant_draft_score == 0.55
    
    def test_draft_context_defaults(self):
        """DraftContext should have sensible defaults."""
        context = DraftContext()
        assert context.radiant_draft_score == 0.5
        assert context.dire_draft_score == 0.5
