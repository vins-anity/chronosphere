"""
StateManager: Global in-memory state for the Lite Monolith architecture.

This module holds the shared state between the Ingestion API and the Worker.
It replaces Redis for the "Lite" version of Chronosphere.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import math
import random

@dataclass
class DraftContext:
    """Pre-match context from Stratz."""
    radiant_draft_score: float = 0.5  # Win rate of draft
    dire_draft_score: float = 0.5
    radiant_late_game_score: float = 0.5  # Scaling power
    dire_late_game_score: float = 0.5


@dataclass
class MarketOdds:
    """Live odds from PandaScore."""
    radiant_odds: float = 1.9  # Decimal odds
    dire_odds: float = 1.9
    implied_radiant_prob: float = 0.5  # Calculated from odds
    last_updated: Optional[datetime] = None
    is_mock: bool = True


@dataclass
class LiveGameState:
    """Real-time game state from GSI."""
    match_id: Optional[str] = None
    game_time: int = 0
    radiant_gold: int = 0
    dire_gold: int = 0
    radiant_xp: int = 0
    dire_xp: int = 0
    gold_diff: int = 0
    xp_diff: int = 0
    
    # Derived features (calculated by worker)
    networth_velocity: float = 0.0  # Gold change per minute
    networth_gini: float = 0.0  # Concentration of gold
    buyback_power_ratio: float = 0.0
    
    # History for velocity calculation
    gold_history: List[tuple] = field(default_factory=list)  # [(time, gold_diff), ...]
    
    def update_velocity(self):
        """Calculate gold velocity from history (last 60 seconds)."""
        if len(self.gold_history) < 2:
            self.networth_velocity = 0.0
            return
        
        # Get gold diff from 60 seconds ago (or oldest if less)
        now = self.game_time
        target_time = now - 60
        
        old_gold = self.gold_history[0][1]
        for t, g in self.gold_history:
            if t <= target_time:
                old_gold = g
            else:
                break
        
        self.networth_velocity = (self.gold_diff - old_gold) / 60.0  # per second


@dataclass
class SeriesContext:
    """Bo3/Bo5 series state."""
    series_type: str = "bo1"  # bo1, bo3, bo5
    radiant_wins: int = 0
    dire_wins: int = 0
    series_score_diff: int = 0  # radiant_wins - dire_wins


@dataclass
class MatchState:
    """Complete state for a single match."""
    match_id: Optional[str] = None
    is_verified: bool = False  # True if match exists in PandaScore/OpenDota
    is_live: bool = False
    
    draft: DraftContext = field(default_factory=DraftContext)
    market: MarketOdds = field(default_factory=MarketOdds)
    game: LiveGameState = field(default_factory=LiveGameState)
    series: SeriesContext = field(default_factory=SeriesContext)
    
    # Prediction output
    model_win_probability: float = 0.5
    mispricing_index: float = 0.0  # model_prob - market_implied_prob
    
    last_gsi_update: Optional[datetime] = None


class StateManager:
    """
    Singleton state manager for the Lite Monolith architecture.
    
    Thread-safe access to shared state between API and Worker.
    """
    _instance: Optional["StateManager"] = None
    _lock: asyncio.Lock
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = asyncio.Lock()
            cls._instance._current_match: Optional[MatchState] = None
            cls._instance._match_history: Dict[str, MatchState] = {}
        return cls._instance
    
    @property
    def current_match(self) -> Optional[MatchState]:
        return self._current_match
    
    async def start_match(self, match_id: str) -> MatchState:
        """Initialize state for a new match."""
        async with self._lock:
            if self._current_match and self._current_match.match_id:
                # Archive old match
                self._match_history[self._current_match.match_id] = self._current_match
            
            self._current_match = MatchState(match_id=match_id, is_live=True)
            self._current_match.game.match_id = match_id
            return self._current_match
    
    async def update_game_state(self, gsi_data: Dict[str, Any]) -> Optional[MatchState]:
        """Update the live game state from GSI data."""
        async with self._lock:
            if not self._current_match:
                return None
            
            game = self._current_match.game
            map_data = gsi_data.get("map", {})
            
            game.game_time = map_data.get("clock_time", 0)
            
            # Extract gold/xp if available (depends on GSI structure)
            # Standard GSI from player POV vs spectator varies
            if "player" in gsi_data:
                # Single player GSI - limited data
                pass
            
            # Try to get team totals if available
            game.radiant_gold = map_data.get("radiant_gold", game.radiant_gold)
            game.dire_gold = map_data.get("dire_gold", game.dire_gold)
            game.radiant_xp = map_data.get("radiant_xp", game.radiant_xp)
            game.dire_xp = map_data.get("dire_xp", game.dire_xp)
            
            game.gold_diff = game.radiant_gold - game.dire_gold
            game.xp_diff = game.radiant_xp - game.dire_xp
            
            # Update velocity history
            game.gold_history.append((game.game_time, game.gold_diff))
            # Keep only last 2 minutes of history
            cutoff = game.game_time - 120
            game.gold_history = [(t, g) for t, g in game.gold_history if t > cutoff]
            game.update_velocity()
            
            self._current_match.last_gsi_update = datetime.utcnow()
            return self._current_match
    
    async def update_market_odds(self, odds: MarketOdds):
        """Update market odds from PandaScore."""
        async with self._lock:
            if self._current_match:
                self._current_match.market = odds
    
    async def update_draft_context(self, draft: DraftContext):
        """Update draft context from Stratz."""
        async with self._lock:
            if self._current_match:
                self._current_match.draft = draft
    
    async def update_prediction(self, win_prob: float):
        """Update model prediction and calculate mispricing."""
        async with self._lock:
            if self._current_match:
                self._current_match.model_win_probability = win_prob
                market_prob = self._current_match.market.implied_radiant_prob
                self._current_match.mispricing_index = win_prob - market_prob
    
    async def get_broadcast_payload(self) -> Dict[str, Any]:
        """Get the current state as a JSON-serializable dict for WebSocket broadcast."""
        async with self._lock:
            if not self._current_match:
                return {"status": "no_match"}
            
            m = self._current_match
            return {
                "type": "update",
                "match_id": m.match_id,
                "is_verified": m.is_verified,
                "game_time": m.game.game_time,
                "gold_diff": m.game.gold_diff,
                "xp_diff": m.game.xp_diff,
                "networth_velocity": m.game.networth_velocity,
                "model_win_probability": m.model_win_probability,
                "market_implied_probability": m.market.implied_radiant_prob,
                "market_odds_radiant": m.market.radiant_odds,
                "mispricing_index": m.mispricing_index,
                "draft_radiant_score": m.draft.radiant_draft_score,
                "series_score_diff": m.series.series_score_diff,
                "is_mock_odds": m.market.is_mock,
            }


# Global singleton instance
state_manager = StateManager()


class MockMarketGenerator:
    """Generates fake market odds for development."""
    
    @staticmethod
    def generate(game_time: int, gold_diff: int) -> MarketOdds:
        """Generate mock odds that loosely track the game state."""
        # Base probability from gold diff (simplified)
        base_prob = 0.5 + (gold_diff / 50000)  # ±50k gold = edges
        base_prob = max(0.2, min(0.8, base_prob))  # Clamp
        
        # Add some noise to simulate market inefficiency
        noise = random.uniform(-0.05, 0.05)
        implied_prob = base_prob + noise
        implied_prob = max(0.1, min(0.9, implied_prob))
        
        # Convert to decimal odds (with margin)
        margin = 0.05  # 5% bookmaker margin
        radiant_odds = 1 / (implied_prob + margin / 2)
        dire_odds = 1 / ((1 - implied_prob) + margin / 2)
        
        return MarketOdds(
            radiant_odds=round(radiant_odds, 2),
            dire_odds=round(dire_odds, 2),
            implied_radiant_prob=round(implied_prob, 4),
            last_updated=datetime.utcnow(),
            is_mock=True
        )
