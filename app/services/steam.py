"""
Steam Live Service: Fetches live pro matches from Steam Web API.

Uses GetLiveLeagueGames for real-time scoreboard data including:
- Per-player gold, networth, XP
- Kills, deaths, assists
- Game time, tower status

This replaces GSI for a fully web-based live tracking experience.
"""
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from app.core.config import settings
from app.core.redis import RedisClient
import json


@dataclass
class PlayerStats:
    """Per-player live stats from Steam scoreboard."""
    account_id: int
    hero_id: int
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    gold: int = 0
    net_worth: int = 0
    level: int = 1
    gold_per_min: int = 0
    xp_per_min: int = 0


@dataclass
class TeamStats:
    """Team-level aggregated stats."""
    score: int = 0  # Kills
    total_gold: int = 0
    total_networth: int = 0
    tower_state: int = 0
    barracks_state: int = 0
    players: List[PlayerStats] = field(default_factory=list)


@dataclass
class LiveMatch:
    """Live pro match data from Steam."""
    match_id: str
    league_id: int
    league_name: str
    series_id: int
    game_number: int
    game_time: int  # Seconds
    radiant_team_id: int
    radiant_team_name: str
    dire_team_id: int
    dire_team_name: str
    radiant: TeamStats
    dire: TeamStats
    spectators: int
    
    @property
    def gold_diff(self) -> int:
        """Radiant gold advantage (negative = Dire lead)."""
        return self.radiant.total_networth - self.dire.total_networth
    
    @property
    def xp_diff(self) -> int:
        """Estimated XP diff based on levels and kill score."""
        radiant_levels = sum(p.level for p in self.radiant.players)
        dire_levels = sum(p.level for p in self.dire.players)
        # XP per level is roughly 200-300, scale by level difference
        return (radiant_levels - dire_levels) * 250
    
    @property
    def kill_diff(self) -> int:
        """Kill score difference."""
        return self.radiant.score - self.dire.score


class SteamLiveService:
    """Service for fetching live pro matches from Steam Web API."""
    
    BASE_URL = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v1/"
    
    def __init__(self):
        self._cache: List[LiveMatch] = []
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = 5  # seconds (Optimized for Live Pro)
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key from settings (dynamic, not cached at import time)."""
        return settings.STEAM_API_KEY
    
    @property
    def is_available(self) -> bool:
        """Check if Steam API is configured."""
        return bool(self.api_key)
    
    async def get_live_matches(self, use_cache: bool = True) -> List[LiveMatch]:
        """
        Fetch all live pro league matches from Steam.
        
        Returns parsed LiveMatch objects with full scoreboard data.
        """
        if not self.is_available:
            logger.warning("Steam API key not configured")
            return []
        
        # 1. Try Redis Cache (Raw Response)
        raw_cache_key = "steam:raw_live_games"
        games = []
        
        if use_cache:
            try:
                cached_data = await RedisClient.get(raw_cache_key)
                if cached_data:
                    games = json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        # 2. Fetch from API if no cache
        if not games:
            # Check internal memory cache as fallback
            if use_cache and self._cache_time:
                age = (datetime.utcnow() - self._cache_time).total_seconds()
                if age < self._cache_ttl:
                    return self._cache

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.BASE_URL,
                        params={"key": self.api_key},
                        timeout=15.0
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Steam API error: {response.status_code}")
                        return self._cache
                    
                    # Robust decoding for players with special characters in names
                    try:
                        content_str = response.content.decode("utf-8", errors="replace")
                        data = json.loads(content_str)
                    except Exception as json_err:
                        logger.error(f"JSON decode failed: {json_err}")
                        return self._cache
                    games = data.get("result", {}).get("games", [])
                    
                    # Cache successful raw response (TTL 15s)
                    if games:
                        await RedisClient.setex(raw_cache_key, 15, json.dumps(games))
                        
            except Exception as e:
                logger.error(f"Failed to fetch Steam live matches: {e}")
                return self._cache
        
        # 3. Process Games (from Cache or API)
        try:
            matches = []
            for game in games:
                try:
                    match = self._parse_game(game)
                    if not match:
                        continue
                        
                    # QUALITY FILTER:
                    # 1. Check if teams have real names (not default "Radiant"/"Dire")
                    has_default_names = (
                        match.radiant_team_name.lower() in ["radiant", "unknown team", ""] or 
                        match.dire_team_name.lower() in ["dire", "unknown team", ""]
                    )
                    
                    # 2. Check spectator counts
                    is_popular = match.spectators > 5
                    is_very_popular = match.spectators > 500
                    
                    # 3. Apply filter:
                    # - Real team names: ALWAYS include (even drafting with 0 spectators)
                    # - Default names: Only if very popular (>500 spectators)
                    if has_default_names:
                        if not is_very_popular:
                            continue
                    # Real team names pass through regardless of spectator count
                        
                    matches.append(match)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse game: {e}")
                    continue
            
            # Update cache
            self._cache = matches
            self._cache_time = datetime.utcnow()
            
            logger.info(f"Fetched {len(matches)} live pro matches from Steam")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to process Steam matches: {e}")
            return self._cache
    
    def _parse_game(self, game: Dict[str, Any]) -> Optional[LiveMatch]:
        """Parse a single game from Steam API response."""
        # Must have scoreboard for useful data
        # Parse teams
        radiant_team = game.get("radiant_team", {})
        dire_team = game.get("dire_team", {})

        # Handle Draft Phase (No Scoreboard)
        scoreboard = game.get("scoreboard")
        if not scoreboard:
            # Create empty stats for drafting phase
            radiant_data = {}
            dire_data = {}
            duration = 0
            # Only proceed if we at least have team names (Drafting Pro Match)
            if not radiant_team or not dire_team:
                return None
        else:
            radiant_data = scoreboard.get("radiant", {})
            dire_data = scoreboard.get("dire", {})
            duration = int(scoreboard.get("duration", 0))
        
        return LiveMatch(
            match_id=str(game.get("match_id", "")),
            league_id=game.get("league_id", 0),
            league_name=game.get("league_name", "Unknown League"),
            series_id=game.get("series_id", 0),
            game_number=game.get("game_number", 1),
            game_time=duration,
            radiant_team_id=radiant_team.get("team_id", 0),
            radiant_team_name=radiant_team.get("team_name", "Radiant"),
            dire_team_id=dire_team.get("team_id", 0),
            dire_team_name=dire_team.get("team_name", "Dire"),
            radiant=self._parse_team_stats(radiant_data),
            dire=self._parse_team_stats(dire_data),
            spectators=game.get("spectators", 0),
        )
    
    def _parse_team_stats(self, team_data: Dict[str, Any]) -> TeamStats:
        """Parse team stats from scoreboard."""
        players = []
        for p in team_data.get("players", []):
            players.append(PlayerStats(
                account_id=p.get("account_id", 0),
                hero_id=p.get("hero_id", 0),
                kills=p.get("kills", 0),
                deaths=p.get("deaths", 0),
                assists=p.get("assists", 0),
                last_hits=p.get("last_hits", 0),
                denies=p.get("denies", 0),
                gold=p.get("gold", 0),
                net_worth=p.get("net_worth", 0),
                level=p.get("level", 1),
                gold_per_min=p.get("gold_per_min", 0),
                xp_per_min=p.get("xp_per_min", 0),
            ))
        
        return TeamStats(
            score=team_data.get("score", 0),
            total_gold=sum(p.gold for p in players),
            total_networth=sum(p.net_worth for p in players),
            tower_state=team_data.get("tower_state", 0),
            barracks_state=team_data.get("barracks_state", 0),
            players=players,
        )
    
    def to_feature_input(self, match: LiveMatch) -> Dict[str, Any]:
        """
        Convert LiveMatch to feature extractor input format.
        
        Returns a GSI-compatible dict for the ML pipeline.
        """
        return {
            "provider": {
                "name": "Steam API",
                "timestamp": int(datetime.utcnow().timestamp())
            },
            "map": {
                "matchid": match.match_id,
                "clock_time": match.game_time,
                "game_time": match.game_time,
                "radiant_score": match.radiant.score,
                "dire_score": match.dire.score,
                "radiant_gold": match.radiant.total_networth,
                "dire_gold": match.dire.total_networth,
                "radiant_xp": sum(p.xp_per_min * match.game_time // 60 for p in match.radiant.players),
                "dire_xp": sum(p.xp_per_min * match.game_time // 60 for p in match.dire.players),
            },
            # Include extended player data for advanced features
            "players": {
                "radiant": [
                    {
                        "hero_id": p.hero_id,
                        "net_worth": p.net_worth,
                        "gold": p.gold,
                        "level": p.level,
                        "kills": p.kills,
                        "deaths": p.deaths,
                        "assists": p.assists,
                    }
                    for p in match.radiant.players
                ],
                "dire": [
                    {
                        "hero_id": p.hero_id,
                        "net_worth": p.net_worth,
                        "gold": p.gold,
                        "level": p.level,
                        "kills": p.kills,
                        "deaths": p.deaths,
                        "assists": p.assists,
                    }
                    for p in match.dire.players
                ],
            },
        }

# Lazy singleton - instantiated on first access, not at import time
_steam_service_instance: Optional[SteamLiveService] = None

def get_steam_service() -> SteamLiveService:
    """Get the Steam service singleton, lazily initialized."""
    global _steam_service_instance
    if _steam_service_instance is None:
        _steam_service_instance = SteamLiveService()
    return _steam_service_instance

# For backwards compatibility - this is a property-like access pattern
# that defers instantiation until actual use
class _SteamServiceProxy:
    """Proxy object that lazily accesses the real steam service."""
    
    def __getattr__(self, name):
        return getattr(get_steam_service(), name)

steam_service = _SteamServiceProxy()
