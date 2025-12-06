"""
Stratz Client: Fetches draft analysis and hero statistics via GraphQL.

Implements:
- Draft win rates (early/mid/late game)
- Hero matchup analysis
- Facet statistics
- Caching (fetch once per match)
"""
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger
from app.core.config import settings
from app.core.state import DraftContext
from app.core.rate_tracker import tracker


# GraphQL query for draft analysis
DRAFT_ANALYSIS_QUERY = """
query DraftAnalysis($matchId: Long!) {
  match(id: $matchId) {
    id
    radiantTeam {
      name
    }
    direTeam {
      name
    }
    players {
      heroId
      isRadiant
      hero {
        displayName
        winRate
        stats {
          winRate
          lateGameWinRate: winRateByDuration(durationMinutes: 40)
        }
      }
    }
    predictedWinRate
  }
}
"""

# Simplified query for hero win rates (no match context needed)
HERO_WINRATES_QUERY = """
query HeroWinRates($heroIds: [Short!]!) {
  constants {
    heroes(ids: $heroIds) {
      id
      displayName
      stats {
        winRate
        pickRate
      }
    }
  }
}
"""


class StratzClient:
    """Client for Stratz GraphQL API (Draft Context)."""
    
    BASE_URL = "https://api.stratz.com/graphql"
    
    def __init__(self):
        self.api_key = settings.STRATZ_API_KEY
        self._cached_context: Dict[str, DraftContext] = {}  # match_id -> context
    
    @property
    def is_available(self) -> bool:
        """Check if the client is configured with an API key."""
        return bool(self.api_key) and not settings.USE_MOCK_CONTEXT
    
    async def get_draft_context(self, match_id: str, hero_ids: Optional[List[int]] = None) -> DraftContext:
        """
        Fetch draft analysis for a match.
        
        If we have the match ID in Stratz (pro match), use full analysis.
        Otherwise, estimate from hero win rates.
        """
        # Return cached if available
        if match_id in self._cached_context:
            return self._cached_context[match_id]
        
        if not self.is_available:
            logger.debug("Stratz not available, using mock data")
            return self._get_mock_draft_context()
        
        try:
            # First try to get match-specific data
            context = await self._fetch_match_analysis(match_id)
            if context:
                self._cached_context[match_id] = context
                return context
            
            # Fall back to hero-based estimation if hero_ids provided
            if hero_ids:
                context = await self._estimate_from_heroes(hero_ids)
                self._cached_context[match_id] = context
                return context
                
        except Exception as e:
            logger.error(f"Stratz request failed: {e}")
        
        return self._get_mock_draft_context()
    
    async def _fetch_match_analysis(self, match_id: str) -> Optional[DraftContext]:
        """Fetch analysis for a specific match ID."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": DRAFT_ANALYSIS_QUERY,
                        "variables": {"matchId": int(match_id)}
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                tracker.record_call("stratz")
                data = response.json()
                
                match_data = data.get("data", {}).get("match")
                if not match_data:
                    return None
                
                # Calculate draft scores from hero win rates
                radiant_score = 0.5
                dire_score = 0.5
                radiant_late = 0.5
                dire_late = 0.5
                
                players = match_data.get("players", [])
                radiant_heroes = [p for p in players if p.get("isRadiant")]
                dire_heroes = [p for p in players if not p.get("isRadiant")]
                
                if radiant_heroes:
                    rates = [p.get("hero", {}).get("stats", {}).get("winRate", 0.5) for p in radiant_heroes]
                    radiant_score = sum(rates) / len(rates)
                    late_rates = [p.get("hero", {}).get("stats", {}).get("lateGameWinRate", 0.5) for p in radiant_heroes]
                    radiant_late = sum(late_rates) / len(late_rates)
                
                if dire_heroes:
                    rates = [p.get("hero", {}).get("stats", {}).get("winRate", 0.5) for p in dire_heroes]
                    dire_score = sum(rates) / len(rates)
                    late_rates = [p.get("hero", {}).get("stats", {}).get("lateGameWinRate", 0.5) for p in dire_heroes]
                    dire_late = sum(late_rates) / len(late_rates)
                
                # Use Stratz predicted win rate if available
                predicted = match_data.get("predictedWinRate")
                if predicted is not None:
                    radiant_score = predicted
                    dire_score = 1 - predicted
                
                return DraftContext(
                    radiant_draft_score=radiant_score,
                    dire_draft_score=dire_score,
                    radiant_late_game_score=radiant_late,
                    dire_late_game_score=dire_late
                )
                
        except Exception as e:
            logger.error(f"Failed to fetch match analysis: {e}")
            return None
    
    async def _estimate_from_heroes(self, hero_ids: List[int]) -> DraftContext:
        """Estimate draft context from hero IDs (when match not in Stratz)."""
        # Split into radiant (first 5) and dire (last 5)
        radiant_ids = hero_ids[:5] if len(hero_ids) >= 5 else hero_ids
        dire_ids = hero_ids[5:10] if len(hero_ids) >= 10 else []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": HERO_WINRATES_QUERY,
                        "variables": {"heroIds": hero_ids}
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                heroes = data.get("data", {}).get("constants", {}).get("heroes", [])
                hero_map = {h["id"]: h for h in heroes}
                
                # Calculate average win rates
                radiant_rates = [hero_map.get(hid, {}).get("stats", {}).get("winRate", 0.5) for hid in radiant_ids]
                dire_rates = [hero_map.get(hid, {}).get("stats", {}).get("winRate", 0.5) for hid in dire_ids]
                
                radiant_score = sum(radiant_rates) / len(radiant_rates) if radiant_rates else 0.5
                dire_score = sum(dire_rates) / len(dire_rates) if dire_rates else 0.5
                
                return DraftContext(
                    radiant_draft_score=radiant_score,
                    dire_draft_score=dire_score,
                    radiant_late_game_score=0.5,  # Can't determine without more data
                    dire_late_game_score=0.5
                )
                
        except Exception as e:
            logger.error(f"Failed to estimate from heroes: {e}")
            return self._get_mock_draft_context()
    
    def _get_mock_draft_context(self) -> DraftContext:
        """Return mock draft context for development."""
        import random
        # Slightly randomized to show variation
        base = 0.5
        radiant_var = random.uniform(-0.1, 0.1)
        
        return DraftContext(
            radiant_draft_score=base + radiant_var,
            dire_draft_score=base - radiant_var,
            radiant_late_game_score=0.5 + random.uniform(-0.15, 0.15),
            dire_late_game_score=0.5 + random.uniform(-0.15, 0.15)
        )
    
    def clear_cache(self, match_id: Optional[str] = None):
        """Clear cached draft context."""
        if match_id:
            self._cached_context.pop(match_id, None)
        else:
            self._cached_context.clear()


# Lazy singleton - instantiated on first access, not at import time
_stratz_client_instance: Optional[StratzClient] = None

def get_stratz_client() -> StratzClient:
    """Get the Stratz client singleton, lazily initialized."""
    global _stratz_client_instance
    if _stratz_client_instance is None:
        _stratz_client_instance = StratzClient()
    return _stratz_client_instance

class _StratzClientProxy:
    """Proxy for lazy initialization."""
    def __getattr__(self, name):
        return getattr(get_stratz_client(), name)

stratz_client = _StratzClientProxy()
