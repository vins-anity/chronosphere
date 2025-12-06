"""
OpenDota Collector: Fetches training data from OpenDota API.

Implements:
- Team history for momentum score
- Linear interpolation of minute-data to second-data
- Rate limit handling with backoff
- API quota tracking
"""
import asyncio
import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from app.core.config import settings
from app.core.rate_tracker import tracker
from app.services.stratz import stratz_client


class OpenDotaCollector:
    """Collects training data from OpenDota API."""
    
    BASE_URL = "https://api.opendota.com/api"
    DATA_DIR = Path("data")
    RAW_DIR = DATA_DIR / "raw"
    PROCESSED_DIR = DATA_DIR / "processed"
    
    def __init__(self):
        self.api_key = settings.OPENDOTA_API_KEY
        self._request_count = 0
        self._last_request_time: Optional[datetime] = None
        
        # Create data directories
        self.RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        self.team_stats_cache: Dict[int, Dict[str, float]] = {}  # team_id -> {pace, aggression}

    async def get_team_stats(self, team_id: int) -> Dict[str, float]:
        """Get or fetch team playstyle stats."""
        if not team_id:
            return {"pace": 0.5, "aggression": 0.0}
            
        if team_id in self.team_stats_cache:
            return self.team_stats_cache[team_id]
            
        # Fetch history
        history = await self.fetch_team_history(team_id, limit=20)
        if not history:
            stats = {"pace": 0.5, "aggression": 0.0, "winrate": 0.5}
            self.team_stats_cache[team_id] = stats
            return stats
            
        # Calculate metrics
        durations = [m.get('duration', 0) for m in history]
        
        # Winrate Calculation (Form)
        wins = 0
        valid_games = 0
        for m in history:
            # 'radiant' field in /teams/matches is boolean: True if team was Radiant
            was_radiant = m.get('radiant')
            radiant_win = m.get('radiant_win')
            
            if was_radiant is not None and radiant_win is not None:
                if was_radiant == radiant_win:
                    wins += 1
                valid_games += 1
        
        winrate = wins / valid_games if valid_games > 0 else 0.5
        
        avg_duration = sum(durations) / len(durations) if durations else 2400
        # Normalize Pace: 0 = Fast (20m), 1 = Slow (60m)
        # 1200s to 3600s range
        pace = (avg_duration - 1200) / (3600 - 1200)
        pace = max(0.0, min(1.0, pace))
        
        # Aggression: We might not get kills easily without fetching match details.
        # Let's stick to Pace for "High Quality" without partial data.
        aggression = 0.0 
        
        stats = {"pace": pace, "aggression": aggression, "winrate": winrate}
        self.team_stats_cache[team_id] = stats
        return stats
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited request to OpenDota."""
        # Check quota before making request
        if not tracker.can_call("opendota"):
            logger.error("OpenDota quota exceeded - aborting request")
            return None
        
        # Rate limiting: 60 requests per minute for free tier
        if self._last_request_time:
            elapsed = (datetime.utcnow() - self._last_request_time).total_seconds()
            if elapsed < 1.0:  # At least 1 second between requests
                await asyncio.sleep(1.0 - elapsed)
        
        try:
            params = params or {}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}{endpoint}",
                    params=params,
                    timeout=30.0
                )
                
                self._last_request_time = datetime.utcnow()
                self._request_count += 1
                
                # Record successful request to tracker
                tracker.record_call("opendota")
                
                if response.status_code == 429:
                    # Rate limited - back off
                    logger.warning("Rate limited by OpenDota, sleeping 10s...")
                    await asyncio.sleep(10)
                    return await self._make_request(endpoint, params)
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"OpenDota request failed: {e}")
            return None
    
    async def fetch_pro_matches(self, limit: int = 100) -> List[Dict]:
        """Fetch recent pro matches."""
        logger.info(f"Fetching {limit} pro matches...")
        matches = await self._make_request("/proMatches")
        
        if not matches:
            return []
        
        return matches[:limit]
    

    
    async def fetch_match_details(self, match_id: int) -> Optional[Dict]:
        """Fetch detailed match data including gold/xp advantages."""
        return await self._make_request(f"/matches/{match_id}")
    
    async def fetch_team_history(self, team_id: int, limit: int = 20) -> List[Dict]:
        """Fetch team's recent match history for momentum calculation."""
        matches = await self._make_request(f"/teams/{team_id}/matches")
        if not matches:
            return []
        return matches[:limit]
    
    def interpolate_minute_data(self, minute_data: List[int]) -> List[int]:
        """
        Linear interpolate minute-data to second-data.
        
        Input: [0, 100, 300] (values at minutes 0, 1, 2)
        Output: [0, 1, 2, ..., 99, 100, 101, ..., 299, 300] (values per second)
        """
        if len(minute_data) < 2:
            return minute_data * 60 if minute_data else []
        
        interpolated = []
        for i in range(len(minute_data) - 1):
            start_val = minute_data[i]
            end_val = minute_data[i + 1]
            
            # Interpolate 60 seconds between each minute
            for sec in range(60):
                t = sec / 60.0
                val = int(start_val + (end_val - start_val) * t)
                interpolated.append(val)
        
        # Add the final value
        interpolated.append(minute_data[-1])
        
        return interpolated
    
    def calculate_velocity_series(self, gold_adv: List[int], window: int = 60) -> List[float]:
        """Calculate gold velocity (change per second) for each point."""
        if len(gold_adv) < window:
            return [0.0] * len(gold_adv)
        
        velocities = [0.0] * window  # First 'window' seconds have no velocity
        
        for i in range(window, len(gold_adv)):
            diff = gold_adv[i] - gold_adv[i - window]
            velocity = diff / window  # Per second
            velocities.append(velocity)
        
        return velocities
    
    async def collect_training_data(self, num_matches: int = 500, save: bool = True) -> List[Dict]:
        """
        Collect and process training data.
        
        Returns list of training rows with interpolated features.
        """
        logger.info(f"Starting data collection for {num_matches} matches...")
        
        # Fetch match IDs
        pro_matches = await self.fetch_pro_matches(limit=num_matches)
        
        if not pro_matches:
            logger.error("No matches found")
            return []
        
        training_rows = []
        processed = 0
        
        for match in pro_matches:
            match_id = match.get("match_id")
            if not match_id:
                continue
            
            logger.info(f"Processing match {match_id} ({processed + 1}/{len(pro_matches)})")
            
            details = await self.fetch_match_details(match_id)
            if not details:
                continue
            
            try:
                # We convert match_id to str as stratz_client expects
                draft_ctx = await stratz_client.get_draft_context(str(match_id))
            except Exception as e:
                logger.warning(f"Failed to fetch Stratz context for {match_id}: {e}")
            
            # Fetch Team Stats
            radiant_stats = await self.get_team_stats(details.get("radiant_team_id"))
            dire_stats = await self.get_team_stats(details.get("dire_team_id"))

            rows = self._process_match_enhanced(
                details, 
                draft_context=draft_ctx,
                radiant_stats=radiant_stats,
                dire_stats=dire_stats
            )
            training_rows.extend(rows)
            processed += 1
            
            # Save periodically
            if save and processed % 10 == 0:
                self._save_training_data(training_rows)
        
        if save:
            self._save_training_data(training_rows)
        
        logger.info(f"Collected {len(training_rows)} training rows from {processed} matches")
        return training_rows
    
    async def collect_matches_in_range(
        self, 
        since_date: str = "2025-09-04",  # TI 2025 start
        until_date: str = None,
        limit: int = 500,
        save: bool = True
    ) -> List[Dict]:
        """
        Collect pro matches within a date range.
        
        Args:
            since_date: Start date (YYYY-MM-DD), default TI 2025
            until_date: End date (YYYY-MM-DD), default today
            limit: Max matches to collect
            save: Whether to save to file
        
        Returns:
            List of training rows
        """
        from datetime import datetime as dt
        
        since_ts = int(dt.strptime(since_date, "%Y-%m-%d").timestamp())
        until_ts = int(dt.now().timestamp()) if not until_date else int(dt.strptime(until_date, "%Y-%m-%d").timestamp())
        
        logger.info(f"Collecting pro matches from {since_date} to {until_date or 'today'}")
        
        all_matches = []
        last_match_id = None
        
        # Paginate through pro matches (OpenDota returns newest first)
        while len(all_matches) < limit:
            params = {}
            if last_match_id:
                params["less_than_match_id"] = last_match_id
            
            batch = await self._make_request("/proMatches", params)
            if not batch:
                break
            
            # Filter by date range
            for match in batch:
                match_time = match.get("start_time", 0)
                if since_ts <= match_time <= until_ts:
                    all_matches.append(match)
                
                if len(all_matches) >= limit:
                    break
            
            # Check if we've gone past our date range
            oldest_in_batch = min(m.get("start_time", 0) for m in batch)
            if oldest_in_batch < since_ts:
                break
            
            last_match_id = min(m.get("match_id", 0) for m in batch)
            
            logger.info(f"Fetched batch, total matches in range: {len(all_matches)}")
        
        logger.info(f"Found {len(all_matches)} matches in date range")
        
        # Process matches into training data
        training_rows = []
        for i, match in enumerate(all_matches):
            match_id = match.get("match_id")
            if not match_id:
                continue
            
            logger.info(f"Processing match {match_id} ({i + 1}/{len(all_matches)})")
            
            details = await self.fetch_match_details(match_id)
            if not details:
                continue
            
            # Fetch Facet-Aware Draft Context via Stratz
            draft_ctx = None
            try:
                draft_ctx = await stratz_client.get_draft_context(str(match_id))
            except Exception:
                pass

            rows = self._process_match_enhanced(details, draft_context=draft_ctx)
            training_rows.extend(rows)
            
            if save and (i + 1) % 10 == 0:
                self._save_training_data(training_rows)
        
        if save:
            self._save_training_data(training_rows)
        
        logger.info(f"Collected {len(training_rows)} training rows from {len(all_matches)} matches")
        return training_rows

    def _process_match_enhanced(
        self, 
        match_data: Dict, 
        draft_context: Optional[Any] = None,
        radiant_stats: Optional[Dict] = None,
        dire_stats: Optional[Dict] = None
    ) -> List[Dict]:
        """Process match with enhanced features for better accuracy."""
        rows = []
        
        # Extract key data
        radiant_win = match_data.get("radiant_win", False)
        duration = match_data.get("duration", 0)
        start_time = match_data.get("start_time", 0)
        
        # Draft Scores (Facet-Aware via Stratz)
        draft_score_diff = 0.0
        late_game_score_diff = 0.0
        if draft_context:
            draft_score_diff = draft_context.radiant_draft_score - draft_context.dire_draft_score
            late_game_score_diff = draft_context.radiant_late_game_score - draft_context.dire_late_game_score
            
        # Team Metrics (Playstyle & Form)
        r_stats = radiant_stats or {"pace": 0.5, "aggression": 0.0, "winrate": 0.5}
        d_stats = dire_stats or {"pace": 0.5, "aggression": 0.0, "winrate": 0.5}
        
        radiant_gold_adv = match_data.get("radiant_gold_adv", [])
        radiant_xp_adv = match_data.get("radiant_xp_adv", [])
        
        if not radiant_gold_adv:
            return rows
            
        # Extract per-player gold time series (if available)
        players = match_data.get("players", [])
        
        # Pre-process player gold arrays
        player_gold_ts = []
        for p in players:
            g_t = p.get('gold_t', [])
            if g_t:
                player_gold_ts.append({
                    'is_radiant': p.get("isRadiant", p.get("player_slot", 128) < 128),
                    'gold_t': self.interpolate_minute_data(g_t)
                })

        # Total team kills (final) - Used for linear estimation
        total_radiant_kills = sum(p.get("kills", 0) for p in players if p.get("isRadiant", p.get("player_slot", 128) < 128))
        total_dire_kills = sum(p.get("kills", 0) for p in players if not p.get("isRadiant", p.get("player_slot", 128) < 128))
        
        # Interpolate Advantages
        gold_series = self.interpolate_minute_data(radiant_gold_adv)
        xp_series = self.interpolate_minute_data(radiant_xp_adv) if radiant_xp_adv else [0] * len(gold_series)
        velocity_series = self.calculate_velocity_series(gold_series)
        
        # Benchmarks for Carry Efficiency
        benchmarks = {600: 4000, 1200: 10000, 1800: 18000, 2400: 28000, 3000: 38000, 3600: 50000}
        
        # Generate a training row every 30 seconds
        for sec in range(0, len(gold_series), 30):
            if sec >= duration:
                break
            
            # 1. Kills Estimate
            time_ratio = sec / duration if duration > 0 else 0
            kills_diff_est = int((total_radiant_kills - total_dire_kills) * time_ratio)
            
            # 2. Gini Coefficient (Real Calculation)
            gini = 0.0
            if player_gold_ts:
                current_nws = []
                is_radiant_leading = gold_series[sec] >= 0
                for p_data in player_gold_ts:
                    if p_data['is_radiant'] == is_radiant_leading:
                        t_idx = min(sec, len(p_data['gold_t']) - 1)
                        current_nws.append(p_data['gold_t'][t_idx])
                
                if current_nws and sum(current_nws) > 0:
                    current_nws.sort()
                    n = len(current_nws)
                    cumulative = 0
                    gini_sum = 0
                    for i, nw in enumerate(current_nws):
                        cumulative += nw
                        gini_sum += (2 * (i + 1) - n - 1) * nw
                    gini = gini_sum / (n * sum(current_nws))
            
            # 3. Carry Efficiency
            efficiency = 1.0
            if player_gold_ts:
                # Identify carry (highest NW on Radiant)
                radiant_nws = [
                    p['gold_t'][min(sec, len(p['gold_t']) - 1)] 
                    for p in player_gold_ts if p['is_radiant']
                ]
                if radiant_nws:
                    max_nw = max(radiant_nws)
                    # Find benchmark
                    bench = benchmarks[3600]
                    for t_mark, gold_mark in sorted(benchmarks.items()):
                        if sec <= t_mark:
                            bench = gold_mark
                            break
                    efficiency = max(0.5, min(2.0, max_nw / bench)) if bench > 0 else 1.0

            row = {
                "match_id": match_data.get("match_id"),
                "start_time": start_time,
                "game_time": sec,
                "game_time_normalized": min(1.0, sec / 3600.0),
                "gold_diff": gold_series[sec],
                "gold_diff_normalized": max(-1.0, min(1.0, gold_series[sec] / 50000.0)),
                "xp_diff": xp_series[sec] if sec < len(xp_series) else 0,
                "xp_diff_normalized": max(-1.0, min(1.0, (xp_series[sec] if sec < len(xp_series) else 0) / 30000.0)),
                "networth_velocity": velocity_series[sec] if sec < len(velocity_series) else 0.0,
                "networth_gini": gini,
                "buyback_power_ratio": 0.0,
                "draft_score_diff": draft_score_diff,
                "late_game_score_diff": late_game_score_diff, 
                "series_score_diff": 0.0,
                "carry_efficiency_index": efficiency,
                "radiant_pace_score": r_stats["pace"],
                "dire_pace_score": d_stats["pace"],
                "radiant_aggression_score": r_stats["aggression"],
                "dire_aggression_score": d_stats["aggression"],
                "radiant_recent_winrate": r_stats["winrate"],
                "dire_recent_winrate": d_stats["winrate"],
                "kills_diff": kills_diff_est,
                "radiant_pace_score": r_stats["pace"],
                "dire_pace_score": d_stats["pace"],
                "radiant_aggression_score": r_stats["aggression"],
                "dire_aggression_score": d_stats["aggression"],
                "radiant_recent_winrate": r_stats["winrate"],
                "dire_recent_winrate": d_stats["winrate"],
                "kills_diff": kills_diff_est,
                "kills_diff_normalized": max(-1.0, min(1.0, kills_diff_est / 30.0)),
                "radiant_win": 1 if radiant_win else 0,
            }
            rows.append(row)
        
        return rows
    
    def _process_match(self, match_data: Dict) -> List[Dict]:
        """Wrapper for enhanced process (legacy support)."""
        return self._process_match_enhanced(match_data)
    
    def _save_training_data(self, rows: List[Dict]):
        """Save training data to file."""
        filepath = self.PROCESSED_DIR / "training_data.jsonl"
        with open(filepath, "w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        logger.info(f"Saved {len(rows)} rows to {filepath}")


# CLI entry point
async def main():
    """Run data collection from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect training data from OpenDota")
    parser.add_argument("--limit", type=int, default=100, help="Number of matches to fetch")
    parser.add_argument("--since", type=str, default=None, 
                       help="Start date (YYYY-MM-DD), e.g. 2025-09-04 for TI 2025")
    parser.add_argument("--until", type=str, default=None,
                       help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--mode", type=str, choices=["quick", "production"], default="quick",
                       help="quick=recent matches, production=date range with enhanced features")
    args = parser.parse_args()
    
    collector = OpenDotaCollector()
    
    if args.mode == "production" or args.since:
        # Production mode: use date range with enhanced features
        since = args.since or "2025-09-04"  # Default to TI 2025
        await collector.collect_matches_in_range(
            since_date=since,
            until_date=args.until,
            limit=args.limit
        )
    else:
        # Quick mode: just grab recent pro matches
        await collector.collect_training_data(num_matches=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
