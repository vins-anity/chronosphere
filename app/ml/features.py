"""
Feature Extractor: Transforms raw GSI data into ML feature vectors.

Implements the "Contextual Alpha" feature set:
- Category A: Team & Player History (Context)
- Category B: Live Economy & Physics (GSI)
- Category C: Advanced "Smart" Features

Feature order must match training data exactly.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger
import math


# Feature names in expected order (must match training)
# Research shows 30-80 features optimal for XGBoost Dota 2 prediction
FEATURE_NAMES = [
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY A: LIVE GAME STATE (16 features)
    # ═══════════════════════════════════════════════════════════════
    
    # Time (2)
    "game_time",
    "game_time_normalized",
    
    # Economy (6)
    "gold_diff",
    "gold_diff_normalized",
    "xp_diff",
    "xp_diff_normalized",
    "networth_velocity",
    "networth_gini",
    
    # Combat (4)
    "kill_diff",
    "kill_diff_normalized",
    "tower_advantage",
    "buyback_power_ratio",
    
    # Momentum & Stability (4)
    "momentum_score",
    "lead_fragility",
    "carry_efficiency_index",
    "fight_win_rate",  # Recent teamfight outcomes
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY B: HERO & DRAFT FEATURES (14 features)
    # ═══════════════════════════════════════════════════════════════
    
    # Hero Winrates (2)
    "radiant_avg_hero_winrate",  # Team's avg hero winrate this patch
    "dire_avg_hero_winrate",
    
    # Draft Quality (4)
    "draft_score_diff",
    "late_game_score_diff",
    "radiant_counter_score",  # How well radiant counters dire
    "dire_counter_score",
    
    # Composition Synergy (4)
    "radiant_synergy_score",  # Internal hero synergy
    "dire_synergy_score",
    "radiant_teamfight_score",  # Teamfight potential
    "dire_teamfight_score",
    
    # Lane Strength (4)
    "radiant_lane_advantage",  # Expected laning phase
    "dire_lane_advantage",
    "radiant_early_game_score",  # Early game power
    "dire_early_game_score",
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY C: PLAYER FEATURES (8 features)
    # ═══════════════════════════════════════════════════════════════
    
    # MMR (3)
    "radiant_avg_mmr",
    "dire_avg_mmr",
    "mmr_diff_normalized",
    
    # Role Performance (4)
    "radiant_core_performance",  # Pos 1-3 avg recent KDA
    "dire_core_performance",
    "radiant_support_performance",  # Pos 4-5 avg performance
    "dire_support_performance",
    
    # Experience (1)
    "hero_experience_diff",  # Games on current heroes
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY D: TEAM HISTORY (10 features)
    # ═══════════════════════════════════════════════════════════════
    
    # Winrates (4)
    "radiant_recent_winrate",
    "dire_recent_winrate",
    "radiant_tournament_winrate",  # Current tournament form
    "dire_tournament_winrate",
    
    # Head-to-Head (2)
    "h2h_radiant_winrate",  # Historical matchup
    "h2h_games_played",  # Sample size indicator
    
    # Consistency (2)
    "radiant_consistency",  # Low variance = consistent team
    "dire_consistency",
    
    # Form & Fatigue (2)
    "radiant_momentum_trend",  # Winning/losing streak
    "dire_momentum_trend",
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY E: MATCH CONTEXT (7 features)
    # ═══════════════════════════════════════════════════════════════
    
    # Series (3)
    "series_score_diff",
    "game_number_in_series",  # 1, 2, 3...
    "is_elimination_game",  # 0 or 1
    
    # Draft Advantage (2)
    "radiant_first_pick",  # 0 or 1
    "pick_phase_advantage",  # Who had better draft position
    
    # Tournament (2)
    "tournament_tier",  # 1=TI, 2=Major, 3=Minor, etc.
    "match_importance",  # Playoff vs group stage
]
# Total: 55 features

# Features used by the currently trained model (13 features)
# This must match FEATURE_COLS in train.py
MODEL_FEATURE_NAMES = [
    "game_time",
    "game_time_normalized",
    "gold_diff",
    "gold_diff_normalized",
    "xp_diff",
    "xp_diff_normalized",
    "networth_velocity",
    "networth_gini",
    "buyback_power_ratio",
    "draft_score_diff",
    "late_game_score_diff",
    "series_score_diff",
    "carry_efficiency_index",
]


@dataclass
class FeatureVector:
    """Typed feature vector - 55 total features for optimal XGBoost performance."""
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY A: LIVE GAME STATE (16 features)
    # ═══════════════════════════════════════════════════════════════
    game_time: float = 0.0
    game_time_normalized: float = 0.0
    gold_diff: float = 0.0
    gold_diff_normalized: float = 0.0
    xp_diff: float = 0.0
    xp_diff_normalized: float = 0.0
    networth_velocity: float = 0.0
    networth_gini: float = 0.0
    kill_diff: float = 0.0
    kill_diff_normalized: float = 0.0
    tower_advantage: float = 0.0
    buyback_power_ratio: float = 0.0
    momentum_score: float = 0.0
    lead_fragility: float = 0.0
    carry_efficiency_index: float = 1.0
    fight_win_rate: float = 0.5
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY B: HERO & DRAFT FEATURES (14 features)
    # ═══════════════════════════════════════════════════════════════
    radiant_avg_hero_winrate: float = 0.5
    dire_avg_hero_winrate: float = 0.5
    draft_score_diff: float = 0.0
    late_game_score_diff: float = 0.0
    radiant_counter_score: float = 0.0
    dire_counter_score: float = 0.0
    radiant_synergy_score: float = 0.0
    dire_synergy_score: float = 0.0
    radiant_teamfight_score: float = 0.0
    dire_teamfight_score: float = 0.0
    radiant_lane_advantage: float = 0.0
    dire_lane_advantage: float = 0.0
    radiant_early_game_score: float = 0.0
    dire_early_game_score: float = 0.0
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY C: PLAYER FEATURES (8 features)
    # ═══════════════════════════════════════════════════════════════
    radiant_avg_mmr: float = 6000.0
    dire_avg_mmr: float = 6000.0
    mmr_diff_normalized: float = 0.0
    radiant_core_performance: float = 0.5
    dire_core_performance: float = 0.5
    radiant_support_performance: float = 0.5
    dire_support_performance: float = 0.5
    hero_experience_diff: float = 0.0
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY D: TEAM HISTORY (10 features)
    # ═══════════════════════════════════════════════════════════════
    radiant_recent_winrate: float = 0.5
    dire_recent_winrate: float = 0.5
    radiant_tournament_winrate: float = 0.5
    dire_tournament_winrate: float = 0.5
    h2h_radiant_winrate: float = 0.5
    h2h_games_played: float = 0.0
    radiant_consistency: float = 0.5
    dire_consistency: float = 0.5
    radiant_momentum_trend: float = 0.0
    dire_momentum_trend: float = 0.0
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY E: MATCH CONTEXT (7 features)
    # ═══════════════════════════════════════════════════════════════
    series_score_diff: float = 0.0
    game_number_in_series: float = 1.0
    is_elimination_game: float = 0.0
    radiant_first_pick: float = 0.0
    pick_phase_advantage: float = 0.0
    tournament_tier: float = 3.0
    match_importance: float = 0.5
    
    def to_list(self) -> List[float]:
        """Convert to list with ALL 55 features (for training)."""
        return [
            # Category A: Live Game State (16)
            self.game_time,
            self.game_time_normalized,
            self.gold_diff,
            self.gold_diff_normalized,
            self.xp_diff,
            self.xp_diff_normalized,
            self.networth_velocity,
            self.networth_gini,
            self.kill_diff,
            self.kill_diff_normalized,
            self.tower_advantage,
            self.buyback_power_ratio,
            self.momentum_score,
            self.lead_fragility,
            self.carry_efficiency_index,
            self.fight_win_rate,
            # Category B: Hero & Draft (14)
            self.radiant_avg_hero_winrate,
            self.dire_avg_hero_winrate,
            self.draft_score_diff,
            self.late_game_score_diff,
            self.radiant_counter_score,
            self.dire_counter_score,
            self.radiant_synergy_score,
            self.dire_synergy_score,
            self.radiant_teamfight_score,
            self.dire_teamfight_score,
            self.radiant_lane_advantage,
            self.dire_lane_advantage,
            self.radiant_early_game_score,
            self.dire_early_game_score,
            # Category C: Player (8)
            self.radiant_avg_mmr,
            self.dire_avg_mmr,
            self.mmr_diff_normalized,
            self.radiant_core_performance,
            self.dire_core_performance,
            self.radiant_support_performance,
            self.dire_support_performance,
            self.hero_experience_diff,
            # Category D: Team History (10)
            self.radiant_recent_winrate,
            self.dire_recent_winrate,
            self.radiant_tournament_winrate,
            self.dire_tournament_winrate,
            self.h2h_radiant_winrate,
            self.h2h_games_played,
            self.radiant_consistency,
            self.dire_consistency,
            self.radiant_momentum_trend,
            self.dire_momentum_trend,
            # Category E: Match Context (7)
            self.series_score_diff,
            self.game_number_in_series,
            self.is_elimination_game,
            self.radiant_first_pick,
            self.pick_phase_advantage,
            self.tournament_tier,
            self.match_importance,
        ]
    
    def to_model_list(self) -> List[float]:
        """Convert to list with only the 13 features the current model expects."""
        return [
            self.game_time,
            self.game_time_normalized,
            self.gold_diff,
            self.gold_diff_normalized,
            self.xp_diff,
            self.xp_diff_normalized,
            self.networth_velocity,
            self.networth_gini,
            self.buyback_power_ratio,
            self.draft_score_diff,
            self.late_game_score_diff,
            self.series_score_diff,
            self.carry_efficiency_index,
        ]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dict for logging/debugging."""
        return {name: val for name, val in zip(FEATURE_NAMES, self.to_list())}



class FeatureExtractor:
    """
    Extracts features from GSI data and StateManager context.
    """
    
    # Normalization constants
    MAX_GAME_TIME = 3600  # 60 minutes in seconds
    MAX_GOLD_DIFF = 50000  # ±50k gold is extreme
    MAX_XP_DIFF = 30000  # ±30k XP is extreme
    
    # Gold benchmarks by time (approximate for Pos1 carry)
    CARRY_GOLD_BENCHMARKS = {
        600: 4000,    # 10 min
        1200: 10000,  # 20 min
        1800: 18000,  # 30 min
        2400: 28000,  # 40 min
        3000: 38000,  # 50 min
        3600: 50000,  # 60 min
    }
    
    def __init__(self):
        self._last_networths: Dict[str, List[int]] = {}  # player_id -> [networth history]
    
    def extract(self, tick: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[float]:
        """
        Extract features from a GSI tick and optional context.
        
        Args:
            tick: GSI data dictionary
            context: Optional context from StateManager (draft, series, etc.)
        
        Returns:
            List of 13 floats for the current model (to_model_list)
        """
        try:
            fv = FeatureVector()
            
            # Time features (2)
            map_data = tick.get('map', {})
            fv.game_time = float(map_data.get('clock_time', 0))
            fv.game_time_normalized = min(1.0, fv.game_time / self.MAX_GAME_TIME)
            
            # Economy features (6)
            fv.gold_diff = self._extract_gold_diff(tick, map_data)
            fv.gold_diff_normalized = max(-1.0, min(1.0, fv.gold_diff / self.MAX_GOLD_DIFF))
            
            fv.xp_diff = self._extract_xp_diff(tick, map_data)
            fv.xp_diff_normalized = max(-1.0, min(1.0, fv.xp_diff / self.MAX_XP_DIFF))
            
            # Velocity (from context if available)
            if context and 'networth_velocity' in context:
                fv.networth_velocity = context['networth_velocity']
            
            # Gini coefficient
            fv.networth_gini = self._calculate_gini(tick)
            
            # Combat features (4)
            radiant_score = float(map_data.get('radiant_score', 0))
            dire_score = float(map_data.get('dire_score', 0))
            fv.kill_diff = radiant_score - dire_score
            # Normalize by expected kills at this game time
            expected_kills = max(1, fv.game_time / 60)  # ~1 kill per minute average
            fv.kill_diff_normalized = max(-1.0, min(1.0, fv.kill_diff / (expected_kills * 2)))
            
            # Tower advantage (simplified - from context or estimate from gold lead)
            if context and 'tower_advantage' in context:
                fv.tower_advantage = context['tower_advantage']
            else:
                # Estimate: Large gold leads usually correlate with tower advantage
                fv.tower_advantage = max(-6.0, min(6.0, fv.gold_diff / 5000))
            
            # Buyback (simplified)
            fv.buyback_power_ratio = self._estimate_buyback_ratio(tick)
            
            # Draft context (2)
            if context:
                fv.draft_score_diff = context.get('draft_score_diff', 0.0)
                fv.late_game_score_diff = context.get('late_game_score_diff', 0.0)
                fv.series_score_diff = context.get('series_score_diff', 0.0)
            
            # Efficiency (1)
            fv.carry_efficiency_index = self._calculate_carry_efficiency(tick, fv.game_time)
            
            # Momentum & Stability (2)
            fv.momentum_score = self._calculate_momentum(tick, context)
            fv.lead_fragility = self._calculate_lead_fragility(fv.gold_diff, fv.game_time, context)
            
            # Team playstyle (6) - from context if available
            if context:
                fv.radiant_pace_score = context.get('radiant_pace_score', 0.5)
                fv.dire_pace_score = context.get('dire_pace_score', 0.5)
                fv.radiant_aggression_score = context.get('radiant_aggression_score', 0.0)
                fv.dire_aggression_score = context.get('dire_aggression_score', 0.0)
                fv.radiant_recent_winrate = context.get('radiant_recent_winrate', 0.5)
                fv.dire_recent_winrate = context.get('dire_recent_winrate', 0.5)
            
            return fv.to_model_list()
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return FeatureVector().to_model_list()  # Return safe defaults
    
    def _calculate_momentum(self, tick: Dict[str, Any], context: Optional[Dict[str, Any]]) -> float:
        """Calculate momentum score (-1 to 1, positive = Radiant momentum)."""
        # Use gold velocity if available
        if context and 'networth_velocity' in context:
            velocity = context['networth_velocity']
            return max(-1.0, min(1.0, velocity / 100))  # Normalize
        
        # Fallback: use kill differential trend
        map_data = tick.get('map', {})
        radiant_score = float(map_data.get('radiant_score', 0))
        dire_score = float(map_data.get('dire_score', 0))
        game_time = float(map_data.get('clock_time', 1))
        
        kill_rate_diff = (radiant_score - dire_score) / max(1, game_time / 60)
        return max(-1.0, min(1.0, kill_rate_diff / 2))
    
    def _calculate_lead_fragility(self, gold_diff: float, game_time: float, context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate how fragile the current lead is (0=stable, 1=fragile).
        
        Factors:
        - Small lead = more fragile
        - Late game = leads more fragile (comebacks easier)
        - High late-game scaling for losing team = more fragile
        """
        abs_lead = abs(gold_diff)
        
        # Base fragility from lead size (smaller lead = more fragile)
        if abs_lead > 15000:
            size_fragility = 0.1  # Very stable
        elif abs_lead > 10000:
            size_fragility = 0.3
        elif abs_lead > 5000:
            size_fragility = 0.5
        else:
            size_fragility = 0.8  # Very fragile
        
        # Time factor (late game = more fragile)
        time_factor = min(1.0, game_time / 2400)  # Peaks at 40 min
        
        # Late game scaling factor
        late_game_factor = 0.0
        if context and 'late_game_score_diff' in context:
            # If losing team has late-game advantage, lead is more fragile
            late_diff = context['late_game_score_diff']
            if (gold_diff > 0 and late_diff < 0) or (gold_diff < 0 and late_diff > 0):
                late_game_factor = abs(late_diff) * 0.3
        
        fragility = size_fragility * 0.5 + time_factor * 0.3 + late_game_factor * 0.2
        return max(0.0, min(1.0, fragility))
    
    def _extract_gold_diff(self, tick: Dict[str, Any], map_data: Dict[str, Any]) -> float:
        """Extract gold difference (Radiant - Dire)."""
        # Try direct team gold first (spectator GSI)
        radiant_gold = map_data.get('radiant_gold', 0)
        dire_gold = map_data.get('dire_gold', 0)
        
        if radiant_gold or dire_gold:
            return float(radiant_gold - dire_gold)
        
        # Try to sum from allplayers if available
        all_players = tick.get('allplayers', tick.get('players', {}))
        if all_players:
            radiant_total = 0
            dire_total = 0
            for player_id, player in all_players.items():
                if isinstance(player, dict):
                    gold = player.get('gold', 0) + player.get('gold_reliable', 0) + player.get('gold_unreliable', 0)
                    team = player.get('team_name', player.get('team', ''))
                    if team == 'radiant' or player.get('team_slot', 10) < 5:
                        radiant_total += gold
                    else:
                        dire_total += gold
            if radiant_total or dire_total:
                return float(radiant_total - dire_total)
        
        return 0.0
    
    def _extract_xp_diff(self, tick: Dict[str, Any], map_data: Dict[str, Any]) -> float:
        """Extract XP difference (Radiant - Dire)."""
        radiant_xp = map_data.get('radiant_xp', 0)
        dire_xp = map_data.get('dire_xp', 0)
        
        if radiant_xp or dire_xp:
            return float(radiant_xp - dire_xp)
        
        return 0.0
    
    def _calculate_gini(self, tick: Dict[str, Any]) -> float:
        """
        Calculate Gini coefficient of networth distribution.
        
        High Gini = Gold concentrated on few heroes (fragile lead)
        Low Gini = Gold spread evenly (resilient)
        
        We calculate for the leading team.
        """
        all_players = tick.get('allplayers', tick.get('players', {}))
        if not all_players:
            return 0.0
        
        # Collect networths by team
        radiant_nw = []
        dire_nw = []
        
        for player_id, player in all_players.items():
            if isinstance(player, dict):
                nw = player.get('net_worth', player.get('gold', 0))
                team = player.get('team_name', player.get('team', ''))
                if team == 'radiant' or player.get('team_slot', 10) < 5:
                    radiant_nw.append(nw)
                else:
                    dire_nw.append(nw)
        
        # Use leading team's distribution
        total_radiant = sum(radiant_nw) if radiant_nw else 0
        total_dire = sum(dire_nw) if dire_nw else 0
        
        if total_radiant > total_dire:
            networths = sorted(radiant_nw)
        else:
            networths = sorted(dire_nw)
        
        if len(networths) < 2:
            return 0.0
        
        # Calculate Gini coefficient
        n = len(networths)
        total = sum(networths)
        if total == 0:
            return 0.0
        
        # Standard Gini formula
        cumulative = 0
        gini_sum = 0
        for i, nw in enumerate(networths):
            cumulative += nw
            gini_sum += (2 * (i + 1) - n - 1) * nw
        
        gini = gini_sum / (n * total)
        return max(0.0, min(1.0, gini))
    
    def _estimate_buyback_ratio(self, tick: Dict[str, Any]) -> float:
        """
        Estimate buyback power ratio.
        
        Positive = Radiant has more buyback gold available
        """
        # This would require full player data with gold amounts
        # For now, return 0 (neutral)
        return 0.0
    
    def _calculate_carry_efficiency(self, tick: Dict[str, Any], game_time: float) -> float:
        """
        Calculate Pos1 carry efficiency vs benchmark.
        
        > 1.0 = Overperforming
        < 1.0 = Underperforming
        """
        # Find the benchmark for current game time
        benchmark = 0
        for time_threshold, gold in sorted(self.CARRY_GOLD_BENCHMARKS.items()):
            if game_time <= time_threshold:
                benchmark = gold
                break
        else:
            benchmark = self.CARRY_GOLD_BENCHMARKS[3600]  # Max benchmark
        
        if benchmark == 0:
            return 1.0
        
        # Try to find Pos1 player networth
        all_players = tick.get('allplayers', tick.get('players', {}))
        if not all_players:
            return 1.0
        
        # Find highest networth player on Radiant (simplified assumption)
        radiant_nws = []
        for player_id, player in all_players.items():
            if isinstance(player, dict):
                team = player.get('team_name', player.get('team', ''))
                if team == 'radiant' or player.get('team_slot', 10) < 5:
                    nw = player.get('net_worth', player.get('gold', 0))
                    radiant_nws.append(nw)
        
        if not radiant_nws:
            return 1.0
        
        carry_nw = max(radiant_nws)
        efficiency = carry_nw / benchmark if benchmark > 0 else 1.0
        
        # Clamp to reasonable range
        return max(0.5, min(2.0, efficiency))


# Singleton for reuse
feature_extractor = FeatureExtractor()
