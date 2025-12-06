"""
OpenDota Client: Fetches live pro matches and league data for verification.

Uses:
- /live - Get top currently ongoing live games (verified pro matches)
- /leagues - Get league metadata for name resolution

This is used to filter Steam matches to only show verified professional games.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from loguru import logger

from app.core.config import settings


@dataclass
class OpenDotaLiveMatch:
    """Live match data from OpenDota."""
    match_id: int
    league_id: int
    league_name: str
    radiant_team_name: str
    dire_team_name: str
    radiant_team_id: int
    dire_team_id: int
    spectators: int
    game_time: int
    average_mmr: int = 0


class OpenDotaClient:
    """Client for OpenDota API (Free tier, no API key required)."""
    
    BASE_URL = "https://api.opendota.com/api"
    
    def __init__(self):
        self.api_key = settings.OPENDOTA_API_KEY  # Optional, for higher rate limits
        self._live_cache: List[OpenDotaLiveMatch] = []
        self._live_cache_time: Optional[datetime] = None
        self._cache_ttl = 30  # seconds
        self._league_cache: Dict[int, str] = {}  # league_id -> name
    
    async def get_live_matches(self, use_cache: bool = True) -> List[OpenDotaLiveMatch]:
        """
        Fetch currently live pro matches from OpenDota.
        
        Returns matches that OpenDota considers "top" live games.
        These are verified professional/high-level matches.
        """
        # Check cache
        if use_cache and self._live_cache_time:
            age = (datetime.utcnow() - self._live_cache_time).total_seconds()
            if age < self._cache_ttl:
                return self._live_cache
        
        try:
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/live",
                    params=params if params else None,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenDota /live error: {response.status_code}")
                    return self._live_cache
                
                data = response.json()
                
            matches = []
            for game in data:
                try:
                    radiant_team = game.get("radiant_team", {}) or {}
                    dire_team = game.get("dire_team", {}) or {}
                    
                    matches.append(OpenDotaLiveMatch(
                        match_id=game.get("match_id", 0),
                        league_id=game.get("league_id", 0),
                        league_name=game.get("league", {}).get("name", "Unknown League") if game.get("league") else "Unknown League",
                        radiant_team_name=radiant_team.get("team_name", "Radiant"),
                        dire_team_name=dire_team.get("team_name", "Dire"),
                        radiant_team_id=radiant_team.get("team_id", 0),
                        dire_team_id=dire_team.get("team_id", 0),
                        spectators=game.get("spectators", 0),
                        game_time=game.get("game_time", 0),
                        average_mmr=game.get("average_mmr", 0),
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse OpenDota live match: {e}")
                    continue
            
            self._live_cache = matches
            self._live_cache_time = datetime.utcnow()
            logger.info(f"OpenDota: Fetched {len(matches)} live pro matches")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenDota live matches: {e}")
            return self._live_cache
    
    async def get_live_match_ids(self) -> Set[int]:
        """Get set of match IDs from OpenDota live endpoint for quick lookup."""
        matches = await self.get_live_matches()
        return {m.match_id for m in matches}
    
    async def get_live_league_ids(self) -> Set[int]:
        """Get set of league IDs from OpenDota live endpoint."""
        matches = await self.get_live_matches()
        return {m.league_id for m in matches if m.league_id > 0}
    
    async def is_verified_pro_match(self, steam_match_id: str, steam_league_id: int) -> bool:
        """
        Check if a Steam match is verified as pro by OpenDota.
        
        Cross-references by match_id or league_id.
        """
        try:
            match_id_int = int(steam_match_id)
        except ValueError:
            return False
        
        matches = await self.get_live_matches()
        
        # Direct match ID lookup
        for m in matches:
            if m.match_id == match_id_int:
                return True
        
        # Fallback: Check if league_id is in OpenDota's live leagues
        live_league_ids = {m.league_id for m in matches if m.league_id > 0}
        if steam_league_id in live_league_ids:
            return True
        
        return False
    
    async def get_league_name(self, league_id: int) -> Optional[str]:
        """Get league name from cache or OpenDota pro matches data."""
        if league_id in self._league_cache:
            return self._league_cache[league_id]
        
        # Try to find in recent pro matches (better data than /live)
        pro_matches = await self.get_recent_pro_matches()
        for m in pro_matches:
            if m.get("leagueid") == league_id:
                league_name = m.get("league_name", "Unknown League")
                self._league_cache[league_id] = league_name
                return league_name
        
        return None
    
    async def get_recent_pro_matches(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch recent pro matches from /proMatches endpoint.
        
        This endpoint has better data than /live:
        - Actual team names (not "Radiant"/"Dire")
        - League names
        - Match IDs
        """
        cache_key = "_pro_matches_cache"
        cache_time_key = "_pro_matches_cache_time"
        
        if use_cache and hasattr(self, cache_key):
            cache_time = getattr(self, cache_time_key, None)
            if cache_time:
                age = (datetime.utcnow() - cache_time).total_seconds()
                if age < self._cache_ttl:
                    return getattr(self, cache_key)
        
        try:
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/proMatches",
                    params=params if params else None,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenDota /proMatches error: {response.status_code}")
                    return getattr(self, cache_key, [])
                
                data = response.json()
                
            # Cache results
            setattr(self, cache_key, data)
            setattr(self, cache_time_key, datetime.utcnow())
            
            # Also populate league cache
            for m in data:
                league_id = m.get("leagueid", 0)
                league_name = m.get("league_name", "")
                if league_id > 0 and league_name:
                    self._league_cache[league_id] = league_name
            
            logger.info(f"OpenDota: Fetched {len(data)} recent pro matches")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenDota pro matches: {e}")
            return getattr(self, cache_key, [])
    
    async def get_pro_match_ids(self) -> Set[int]:
        """Get set of match IDs from recent pro matches."""
        pro_matches = await self.get_recent_pro_matches()
        return {m.get("match_id", 0) for m in pro_matches if m.get("match_id")}
    
    async def get_pro_league_ids(self) -> Set[int]:
        """Get set of league IDs from recent pro matches."""
        pro_matches = await self.get_recent_pro_matches()
        return {m.get("leagueid", 0) for m in pro_matches if m.get("leagueid", 0) > 0}
    
    async def get_team_stats(self, team_id: int) -> Dict[str, Any]:
        """
        Fetch team statistics from OpenDota.
        
        Returns:
            Dict with team info including win rate, recent matches, etc.
        """
        cache_key = f"_team_stats_{team_id}"
        
        # Check cache (cache for 5 minutes)
        if hasattr(self, cache_key):
            cached = getattr(self, cache_key)
            if (datetime.utcnow() - cached.get("_cached_at", datetime.min)).total_seconds() < 300:
                return cached
        
        try:
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/teams/{team_id}",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            
            # Add computed win rate
            wins = data.get("wins", 0)
            losses = data.get("losses", 0)
            total = wins + losses
            data["win_rate"] = wins / total if total > 0 else 0.5
            data["_cached_at"] = datetime.utcnow()
            
            setattr(self, cache_key, data)
            return data
            
        except Exception as e:
            logger.debug(f"Failed to fetch team stats for {team_id}: {e}")
            return {"team_id": team_id, "win_rate": 0.5, "wins": 0, "losses": 0}
    
    async def get_team_recent_form(self, team_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch team's recent match results for form analysis.
        
        Returns:
            Dict with recent win rate, last N results, and momentum score.
        """
        cache_key = f"_team_form_{team_id}"
        
        if hasattr(self, cache_key):
            cached = getattr(self, cache_key)
            if (datetime.utcnow() - cached.get("_cached_at", datetime.min)).total_seconds() < 300:
                return cached
        
        try:
            params = {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/teams/{team_id}/matches",
                    params=params,
                    timeout=10.0
                )
                response.raise_for_status()
                matches = response.json()[:limit]  # Get last N matches
            
            # Calculate recent form
            wins = sum(1 for m in matches if m.get("radiant_win") == (m.get("radiant") == True))
            recent_win_rate = wins / len(matches) if matches else 0.5
            
            # Momentum: weight recent games more heavily
            momentum = 0.0
            for i, m in enumerate(matches[:5]):  # Last 5 games
                weight = 1.0 - (i * 0.15)  # 1.0, 0.85, 0.70, 0.55, 0.40
                won = m.get("radiant_win") == (m.get("radiant") == True)
                momentum += weight * (1 if won else -1)
            momentum = momentum / 3.3  # Normalize to approximately [-1, 1]
            
            result = {
                "team_id": team_id,
                "recent_win_rate": recent_win_rate,
                "last_n_results": len(matches),
                "momentum": max(-1.0, min(1.0, momentum)),
                "_cached_at": datetime.utcnow()
            }
            
            setattr(self, cache_key, result)
            return result
            
        except Exception as e:
            logger.debug(f"Failed to fetch team form for {team_id}: {e}")
            return {"team_id": team_id, "recent_win_rate": 0.5, "momentum": 0.0}


# Lazy singleton - instantiated on first access, not at import time
_opendota_client_instance: Optional[OpenDotaClient] = None

def get_opendota_client() -> OpenDotaClient:
    """Get the OpenDota client singleton, lazily initialized."""
    global _opendota_client_instance
    if _opendota_client_instance is None:
        _opendota_client_instance = OpenDotaClient()
    return _opendota_client_instance

class _OpenDotaClientProxy:
    """Proxy for lazy initialization."""
    def __getattr__(self, name):
        return getattr(get_opendota_client(), name)

opendota_client = _OpenDotaClientProxy()
