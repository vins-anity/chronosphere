"""
PandaScore Client: Fetches live market odds and match verification.

Implements:
- Adaptive Polling (60s pregame, 30s ingame)
- Mock Mode for development
- Rate limit protection
- Upcoming matches support
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from loguru import logger
from app.core.config import settings
from app.core.state import MarketOdds, MockMarketGenerator


class PandaScoreClient:
    """Client for PandaScore API (Market Odds & Match Verification)."""
    
    BASE_URL = "https://api.pandascore.co"
    
    def __init__(self):
        self.api_key = settings.PANDASCORE_API_KEY
        self._last_poll: Optional[datetime] = None
        self._cached_odds: Optional[MarketOdds] = None
        self._cached_matches: List[Dict[str, Any]] = []
        self._cached_upcoming: List[Dict[str, Any]] = []
        
    @property
    def is_available(self) -> bool:
        """Check if the client is configured with an API key."""
        return bool(self.api_key) and not settings.USE_MOCK_ODDS
    
    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Fetch currently running Dota 2 matches."""
        if not self.is_available:
            logger.debug("PandaScore not available, using mock data")
            return self._get_mock_live_matches()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/dota2/matches/running",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                response.raise_for_status()
                self._cached_matches = response.json()
                return self._cached_matches
        except httpx.HTTPStatusError as e:
            logger.error(f"PandaScore API error: {e.response.status_code}")
            return self._cached_matches
        except Exception as e:
            logger.error(f"PandaScore request failed: {e}")
            return self._cached_matches
    
    async def get_upcoming_matches(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch upcoming Dota 2 matches."""
        if not self.is_available:
            logger.debug("PandaScore not available, using mock upcoming data")
            return self._get_mock_upcoming_matches()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/dota2/matches/upcoming",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"per_page": limit},
                    timeout=10.0
                )
                response.raise_for_status()
                self._cached_upcoming = response.json()
                return self._cached_upcoming
        except httpx.HTTPStatusError as e:
            logger.error(f"PandaScore upcoming API error: {e.response.status_code}")
            return self._cached_upcoming
        except Exception as e:
            logger.error(f"PandaScore upcoming request failed: {e}")
            return self._cached_upcoming
    
    async def get_match_odds(self, match_id: str) -> Optional[MarketOdds]:
        """Fetch odds for a specific match."""
        if not self.is_available:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/dota2/matches/{match_id}/odds",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    odds_data = data[0]
                    radiant_odds = odds_data.get("radiant_odds", 1.9)
                    dire_odds = odds_data.get("dire_odds", 1.9)
                    implied_prob = 1 / radiant_odds if radiant_odds > 0 else 0.5
                    
                    self._cached_odds = MarketOdds(
                        radiant_odds=radiant_odds,
                        dire_odds=dire_odds,
                        implied_radiant_prob=implied_prob,
                        last_updated=datetime.utcnow(),
                        is_mock=False
                    )
                    return self._cached_odds
        except Exception as e:
            logger.error(f"Failed to fetch odds: {e}")
        
        return self._cached_odds
    
    async def verify_match(self, match_id: str) -> bool:
        """Check if a match ID is a real pro match."""
        if not self.is_available:
            return False
        
        matches = await self.get_live_matches()
        for match in matches:
            if str(match.get("id")) == match_id:
                return True
            if str(match.get("opendota_match_id")) == match_id:
                return True
        return False
    
    def _get_mock_live_matches(self) -> List[Dict[str, Any]]:
        """Return mock live matches for development."""
        return [
            {
                "id": "mock_live_1",
                "name": "Team Spirit vs Gaimin Gladiators",
                "status": "running",
                "number_of_games": 3,
                "scheduled_at": datetime.utcnow().isoformat(),
                "begin_at": datetime.utcnow().isoformat(),
                "league": {"name": "BLAST Slam V"},
                "tournament": {"name": "BLAST Slam V Grand Finals"},
                "opponents": [
                    {"opponent": {"id": 1, "name": "Team Spirit", "acronym": "TS", "image_url": None}},
                    {"opponent": {"id": 2, "name": "Gaimin Gladiators", "acronym": "GG", "image_url": None}},
                ],
            },
        ]
    
    def _get_mock_upcoming_matches(self) -> List[Dict[str, Any]]:
        """Return mock upcoming matches for development."""
        now = datetime.utcnow()
        return [
            {
                "id": "mock_upcoming_1",
                "name": "Team Falcons vs Team Yandex",
                "status": "not_started",
                "number_of_games": 3,
                "scheduled_at": (now + timedelta(hours=3, minutes=45)).isoformat(),
                "league": {"name": "BLAST Slam V"},
                "tournament": {"name": "BLAST Slam V Playoffs"},
                "opponents": [
                    {"opponent": {"id": 3, "name": "Team Falcons", "acronym": "FLCN", "image_url": None}},
                    {"opponent": {"id": 4, "name": "Team Yandex", "acronym": "YNX", "image_url": None}},
                ],
            },
            {
                "id": "mock_upcoming_2",
                "name": "Tundra Esports vs MOUZ",
                "status": "not_started",
                "number_of_games": 3,
                "scheduled_at": (now + timedelta(hours=7, minutes=45)).isoformat(),
                "league": {"name": "BLAST Slam V"},
                "tournament": {"name": "BLAST Slam V Playoffs"},
                "opponents": [
                    {"opponent": {"id": 5, "name": "Tundra Esports", "acronym": "TUN", "image_url": None}},
                    {"opponent": {"id": 6, "name": "MOUZ", "acronym": "MOUZ", "image_url": None}},
                ],
            },
            {
                "id": "mock_upcoming_3",
                "name": "BetBoom Team vs 1WIN",
                "status": "not_started",
                "number_of_games": 3,
                "scheduled_at": (now + timedelta(hours=10)).isoformat(),
                "league": {"name": "European Pro League"},
                "tournament": {"name": "EPL Season 33"},
                "opponents": [
                    {"opponent": {"id": 7, "name": "BetBoom Team", "acronym": "BB", "image_url": None}},
                    {"opponent": {"id": 8, "name": "1WIN", "acronym": "1WIN", "image_url": None}},
                ],
            },
        ]
    
    def should_poll(self, game_state: str = "in_progress") -> bool:
        """Check if enough time has passed for another poll (adaptive)."""
        if self._last_poll is None:
            return True
        
        interval = (
            settings.MARKET_POLL_INTERVAL_PREGAME 
            if game_state == "pre_game" 
            else settings.MARKET_POLL_INTERVAL_INGAME
        )
        
        elapsed = (datetime.utcnow() - self._last_poll).total_seconds()
        return elapsed >= interval
    
    def mark_polled(self):
        """Mark the current time as the last poll time."""
        self._last_poll = datetime.utcnow()


# Lazy singleton - instantiated on first access, not at import time
_pandascore_client_instance: Optional[PandaScoreClient] = None

def get_pandascore_client() -> PandaScoreClient:
    """Get the PandaScore client singleton, lazily initialized."""
    global _pandascore_client_instance
    if _pandascore_client_instance is None:
        _pandascore_client_instance = PandaScoreClient()
    return _pandascore_client_instance

class _PandaScoreClientProxy:
    """Proxy for lazy initialization."""
    def __getattr__(self, name):
        return getattr(get_pandascore_client(), name)

pandascore_client = _PandaScoreClientProxy()
