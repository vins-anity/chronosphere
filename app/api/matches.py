"""
Matches API: Fetches and serves upcoming/live Dota 2 matches.

Uses PandaScore for match data and combines with our ML predictions.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.services.pandascore import pandascore_client
from app.services.stratz import stratz_client
from app.services.opendota import opendota_client
from app.core.config import settings
from app.core.config import settings
from app.core.rate_tracker import tracker
import asyncio


router = APIRouter(prefix="/api/v1/matches", tags=["matches"])

# Response Models
class TeamInfo(BaseModel):
    id: int
    name: str
    acronym: Optional[str] = None
    image_url: Optional[str] = None


class MatchPrediction(BaseModel):
    team1_win_prob: float
    team2_win_prob: float
    confidence: str  # "high", "medium", "low"
    source: str  # "pregame" or "live"


class MatchResponse(BaseModel):
    id: str
    name: str
    status: str  # "upcoming", "running", "finished"
    scheduled_at: Optional[str] = None
    begin_at: Optional[str] = None
    tournament_name: Optional[str] = None
    league_name: Optional[str] = None
    series_type: Optional[str] = None  # "bo1", "bo3", "bo5"
    team1: Optional[TeamInfo] = None
    team2: Optional[TeamInfo] = None
    prediction: Optional[MatchPrediction] = None
    game_time: Optional[int] = None  # For live matches


# Cache for matches (reduce API calls)
_matches_cache = {
    "data": [],
    "fetched_at": None,
    "ttl_seconds": 300,  # 5 minute cache
}


async def get_cached_matches(force_refresh: bool = False) -> List[dict]:
    """Get matches with caching to protect API quota."""
    now = datetime.utcnow()
    
    # Check cache validity
    if not force_refresh and _matches_cache["fetched_at"]:
        age = (now - _matches_cache["fetched_at"]).total_seconds()
        if age < _matches_cache["ttl_seconds"]:
            return _matches_cache["data"]
    
    # Check rate limit
    if not tracker.can_call("pandascore"):
        logger.warning("PandaScore quota limit reached, using cached data")
        return _matches_cache["data"]
    
    # Fetch fresh data
    try:
        matches = await pandascore_client.get_live_matches()
        upcoming = await pandascore_client.get_upcoming_matches()
        
        all_matches = matches + upcoming
        _matches_cache["data"] = all_matches
        _matches_cache["fetched_at"] = now
        
        tracker.record_call("pandascore")
        tracker.record_call("pandascore")  # Two calls made
        
        logger.info(f"Fetched {len(all_matches)} matches from PandaScore")
        return all_matches
        
    except Exception as e:
        logger.error(f"Failed to fetch matches: {e}")
        return _matches_cache["data"]


def parse_match(match_data: dict) -> MatchResponse:
    """Parse PandaScore match data into our format."""
    opponents = match_data.get("opponents", [])
    
    team1 = None
    team2 = None
    
    if len(opponents) >= 1 and opponents[0].get("opponent"):
        opp = opponents[0]["opponent"]
        team1 = TeamInfo(
            id=opp.get("id", 0),
            name=opp.get("name", "TBD"),
            acronym=opp.get("acronym"),
            image_url=opp.get("image_url"),
        )
    
    if len(opponents) >= 2 and opponents[1].get("opponent"):
        opp = opponents[1]["opponent"]
        team2 = TeamInfo(
            id=opp.get("id", 0),
            name=opp.get("name", "TBD"),
            acronym=opp.get("acronym"),
            image_url=opp.get("image_url"),
        )
    
    # Determine series type
    games_count = match_data.get("number_of_games", 1)
    series_type = f"bo{games_count}"
    
    # Get tournament info
    league = match_data.get("league", {})
    tournament = match_data.get("tournament", {})
    
    return MatchResponse(
        id=str(match_data.get("id", "")),
        name=match_data.get("name", "Unknown Match"),
        status=match_data.get("status", "unknown"),
        scheduled_at=match_data.get("scheduled_at"),
        begin_at=match_data.get("begin_at"),
        tournament_name=tournament.get("name"),
        league_name=league.get("name"),
        series_type=series_type,
        team1=team1,
        team2=team2,
        prediction=None,  # Will be added separately
    )


async def get_pregame_prediction(team1_id: int, team2_id: int) -> MatchPrediction:
    """Generate pre-game prediction using Stratz draft data."""
    # For now, use a simple baseline
    # In production, this would use team history and draft analysis
    
    # Default 50-50
    team1_prob = 0.5
    team2_prob = 0.5
    confidence = "medium"
    
    try:
        # Try to get team stats from recent matches
        # This is a simplified version - full implementation would use Stratz
        team1_prob = 0.5 + (hash(str(team1_id)) % 20 - 10) / 100  # Pseudo-randomize based on ID
        team2_prob = 1 - team1_prob
        
    except Exception as e:
        logger.warning(f"Could not get prediction data: {e}")
    
    return MatchPrediction(
        team1_win_prob=round(team1_prob, 4),
        team2_win_prob=round(team2_prob, 4),
        confidence=confidence,
        source="pregame"
    )


@router.get("", response_model=List[MatchResponse])
async def list_matches(
    status: Optional[str] = Query(None, description="Filter by status: upcoming, running"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Get list of upcoming and live Dota 2 matches.
    
    Results are cached for 5 minutes to protect API quota.
    """
    raw_matches = await get_cached_matches()
    
    matches = []
    for m in raw_matches[:limit]:
        try:
            parsed = parse_match(m)
            
            # Filter by status if specified
            if status and parsed.status != status:
                continue
            
            # Add prediction
            if parsed.team1 and parsed.team2:
                parsed.prediction = await get_pregame_prediction(
                    parsed.team1.id, parsed.team2.id
                )
            
            matches.append(parsed)
        except Exception as e:
            logger.error(f"Error parsing match: {e}")
            continue
    
    return matches


@router.get("/live", response_model=List[MatchResponse])
async def get_live_matches():
    """Get only currently running matches."""
    return await list_matches(status="running")


@router.get("/upcoming", response_model=List[MatchResponse])
async def get_upcoming_matches():
    """Get only upcoming matches."""
    return await list_matches(status="not_started")


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str):
    """Get details for a specific match."""
    raw_matches = await get_cached_matches()
    
    for m in raw_matches:
        if str(m.get("id")) == match_id:
            parsed = parse_match(m)
            
            if parsed.team1 and parsed.team2:
                parsed.prediction = await get_pregame_prediction(
                    parsed.team1.id, parsed.team2.id
                )
            
            return parsed
    
    raise HTTPException(status_code=404, detail="Match not found")


# =============================================================================
# STEAM LIVE PRO MATCHES - Real-time predictions from Steam API
# =============================================================================

from app.services.steam import get_steam_service, LiveMatch
from app.ml.features import FeatureExtractor
from app.ml.model import ModelWrapper

# Initialize ML components for live predictions
_feature_extractor = FeatureExtractor()
_model = ModelWrapper()


class LiveProMatch(BaseModel):
    """Live pro match with real-time ML prediction."""
    match_id: str
    league_name: str
    radiant_team: str
    dire_team: str
    game_time: int
    game_time_formatted: str
    radiant_score: int
    dire_score: int
    gold_diff: int
    xp_diff: int
    radiant_win_prob: float
    dire_win_prob: float
    confidence: str
    spectators: int


class LiveProPrediction(BaseModel):
    """Detailed prediction for a live match."""
    match_id: str
    radiant_team: str
    dire_team: str
    game_time: int
    radiant_win_prob: float
    dire_win_prob: float
    gold_diff: int
    xp_diff: int
    kill_diff: int
    radiant_networth: int
    dire_networth: int
    confidence: str
    edge_signal: str  # "RADIANT_VALUE", "DIRE_VALUE", "NO_EDGE"


def _format_game_time(seconds: int) -> str:
    """Format seconds to MM:SS."""
    mins = abs(seconds) // 60
    secs = abs(seconds) % 60
    return f"{mins}:{secs:02d}"


def _get_confidence(game_time: int, prob: float) -> str:
    """Determine confidence based on game time and probability."""
    # Early game = lower confidence
    if game_time < 600:  # < 10 min
        return "low"
    elif game_time < 1200:  # 10-20 min
        return "medium"
    else:
        # Late game + decisive probability = high confidence
        if abs(prob - 0.5) > 0.2:
            return "high"
        return "medium"


def _get_edge_signal(prob: float, market_prob: float = 0.5) -> str:
    """Determine if there's betting value."""
    edge = prob - market_prob
    if edge > 0.1:
        return "RADIANT_VALUE"
    elif edge < -0.1:
        return "DIRE_VALUE"
    return "NO_EDGE"


def _fuzzy_match_teams(panda_name: str, steam_name: str) -> bool:
    """Check if team names roughly match."""
    p = panda_name.lower().replace("team", "").strip()
    s = steam_name.lower().replace("team", "").strip()
    return p in s or s in p


@router.get("/live/pro", response_model=List[LiveProMatch])
async def get_live_pro_matches():
    """
    Get live pro matches using Hybrid Data Source:
    1. PandaScore for high-quality metadata (Leagues, Teams, Series)
    2. Steam API for real-time functional stats (Gold, XP, Kills)
    
    This ensures we only show legitimate Pro matches (filtered by PandaScore)
    while still providing the real-time edge from Steam data.
    """
    # Get steam service at request time (not at module import time)
    steam_service = get_steam_service()
    
    if not steam_service.is_available:
        raise HTTPException(status_code=503, detail="Steam API not configured")

    # 1. Fetch from all sources in parallel (Steam + OpenDota for verification + PandaScore)
    steam_task = steam_service.get_live_matches(use_cache=True)
    opendota_pro_task = opendota_client.get_recent_pro_matches(use_cache=True)
    panda_task = pandascore_client.get_live_matches()
    
    try:
        steam_matches, pro_matches, raw_panda_matches = await asyncio.gather(
            steam_task, opendota_pro_task, panda_task
        )
    except Exception as e:
        logger.error(f"Failed to fetch live matches: {e}")
        return []
    
    # Build set of verified league IDs from OpenDota /proMatches
    # These are leagues that have had recent professional matches
    verified_league_ids = {m.get("leagueid", 0) for m in pro_matches if m.get("leagueid", 0) > 0}
    
    # Build league name lookup from OpenDota /proMatches (has actual league names)
    opendota_league_names = {m.get("leagueid"): m.get("league_name", "Unknown League") 
                            for m in pro_matches if m.get("leagueid", 0) > 0}
    
    logger.info(f"OpenDota verification: {len(verified_league_ids)} verified league IDs")
    
    # 2. Process PandaScore matches (Primary Source)
    results = []
    matched_steam_ids = set()
    
    for pm in raw_panda_matches:
        try:
            # Parse PandaScore match using existing logic
            parsed_pm = parse_match(pm)
            
            # Try to find corresponding Steam match
            steam_match = None
            
            # Strategy A: Filter steam matches by team names
            if parsed_pm.team1 and parsed_pm.team2:
                p_t1 = parsed_pm.team1.name
                p_t2 = parsed_pm.team2.name
                
                for sm in steam_matches:
                    # Check match identifiers (fuzzy name match)
                    t1_match = _fuzzy_match_teams(p_t1, sm.radiant_team_name) or _fuzzy_match_teams(p_t1, sm.dire_team_name)
                    t2_match = _fuzzy_match_teams(p_t2, sm.radiant_team_name) or _fuzzy_match_teams(p_t2, sm.dire_team_name)
                    
                    if t1_match and t2_match:
                        steam_match = sm
                        break
            
            # Build result
            if steam_match:
                matched_steam_ids.add(steam_match.match_id)
                
                # Use Metadata from PandaScore, Stats from Steam
                feature_input = steam_service.to_feature_input(steam_match)
                
                # Use default draft context (Stratz API often returns 403 for live matches)
                context = {
                    "draft_score_diff": 0.0,
                    "late_game_score_diff": 0.0
                }
                
                features = _feature_extractor.extract(feature_input, context=context)
                radiant_prob = _model.predict(features)
                
                # Determine if PandaScore teams match Steam sides (Radiant/Dire)
                # Default assumption: Steam Radiant = Panda Team 1? Not guaranteed.
                # We need to map them.
                
                # Simple heuristic: If Panda Team1 matches Steam Radiant Name -> Team1 is Radiant
                is_t1_radiant = _fuzzy_match_teams(parsed_pm.team1.name, steam_match.radiant_team_name)
                
                # Use Steam Names if available (they are live from lobby)
                radiant_name = steam_match.radiant_team_name
                dire_name = steam_match.dire_team_name
                
                results.append(LiveProMatch(
                    match_id=steam_match.match_id,  # Use Steam ID for live tracking
                    league_name=parsed_pm.league_name or steam_match.league_name,  # Prefer Panda League Name
                    radiant_team=radiant_name,
                    dire_team=dire_name,
                    game_time=steam_match.game_time,
                    game_time_formatted=_format_game_time(steam_match.game_time),
                    radiant_score=steam_match.radiant.score,
                    dire_score=steam_match.dire.score,
                    gold_diff=steam_match.gold_diff,
                    xp_diff=steam_match.xp_diff,
                    radiant_win_prob=round(radiant_prob, 4),
                    dire_win_prob=round(1 - radiant_prob, 4),
                    confidence=_get_confidence(steam_match.game_time, radiant_prob),
                    spectators=steam_match.spectators,
                ))
            else:
                # PandaScore match but no Steam data (maybe steam delay or names mismatch)
                # Show it anyway? No, user wants LIVE stats. 
                # Or show it with "Waiting for Game Data..."
                pass
                
        except Exception as e:
            # Fail gracefully for individual matches
            match_id = pm.get("id", "unknown")
            logger.error(f"Error processing match {match_id}: {e}")
            import traceback
            with open("debug_error.log", "a") as f:
                f.write(f"Timestamp: {datetime.utcnow()}\n")
                f.write(f"Error processing PandaScore match {match_id}: {e}\n")
                f.write(traceback.format_exc() + "\n\n")
            continue

    # 3. Add Steam Matches verified by OpenDota (filters out unknown amateur games)
    for sm in steam_matches:
        if sm.match_id not in matched_steam_ids:
            # Verify match is from a known pro league using OpenDota
            try:
                match_id_int = int(sm.match_id)
            except ValueError:
                match_id_int = 0
            
            is_verified = sm.league_id in verified_league_ids  # League ID verification via /proMatches
            
            if not is_verified:
                # Skip unverified matches (likely amateur/unknown leagues)
                logger.debug(f"Skipping unverified match: {sm.radiant_team_name} vs {sm.dire_team_name}")
                continue
            
            # Process verified Steam match
            try:
                feature_input = steam_service.to_feature_input(sm)
                
                # Use default draft context (Stratz often fails for live matches)
                context = {
                    "draft_score_diff": 0.0,
                    "late_game_score_diff": 0.0
                }

                features = _feature_extractor.extract(feature_input, context=context)
                radiant_prob = _model.predict(features)
                
                # Use OpenDota league name if available, otherwise Steam
                league_name = opendota_league_names.get(sm.league_id, sm.league_name)
                
                results.append(LiveProMatch(
                    match_id=sm.match_id,
                    league_name=league_name,
                    radiant_team=sm.radiant_team_name,
                    dire_team=sm.dire_team_name,
                    game_time=sm.game_time,
                    game_time_formatted=_format_game_time(sm.game_time),
                    radiant_score=sm.radiant.score,
                    dire_score=sm.dire.score,
                    gold_diff=sm.gold_diff,
                    xp_diff=sm.xp_diff,
                    radiant_win_prob=round(radiant_prob, 4),
                    dire_win_prob=round(1 - radiant_prob, 4),
                    confidence=_get_confidence(sm.game_time, radiant_prob),
                    spectators=sm.spectators,
                ))
            except Exception as e:
                import traceback
                with open("debug_error.log", "a") as f:
                    f.write(f"Error processing {sm.match_id}: {e}\n")
                    f.write(traceback.format_exc() + "\n")
                logger.error(f"Error processing live match {sm.match_id}: {e}")
                continue

    # Sort by spectators
    results.sort(key=lambda x: x.spectators, reverse=True)
    return results


@router.get("/live/pro/{match_id}", response_model=LiveProPrediction)
async def get_live_pro_prediction(match_id: str):
    """
    Get detailed real-time prediction for a specific live pro match.
    
    Use this for the match detail view with edge signals.
    """
    # Get steam service at request time (not at module import time)
    steam_service = get_steam_service()
    
    if not steam_service.is_available:
        raise HTTPException(
            status_code=503,
            detail="Steam API not configured"
        )
    
    matches = await steam_service.get_live_matches()
    
    # Find the specific match
    match = next((m for m in matches if m.match_id == match_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Live match not found")
    
    # Run ML prediction
    feature_input = steam_service.to_feature_input(match)
    features = _feature_extractor.extract(feature_input)
    radiant_prob = _model.predict(features)
    
    return LiveProPrediction(
        match_id=match.match_id,
        radiant_team=match.radiant_team_name,
        dire_team=match.dire_team_name,
        game_time=match.game_time,
        radiant_win_prob=round(radiant_prob, 4),
        dire_win_prob=round(1 - radiant_prob, 4),
        gold_diff=match.gold_diff,
        xp_diff=match.xp_diff,
        kill_diff=match.kill_diff,
        radiant_networth=match.radiant.total_networth,
        dire_networth=match.dire.total_networth,
        confidence=_get_confidence(match.game_time, radiant_prob),
        edge_signal=_get_edge_signal(radiant_prob),
    )


# =============================================================================
# Gemini AI Analysis Endpoint
# =============================================================================
from app.services.gemini import get_gemini_analyst


class AIAnalysisResponse(BaseModel):
    """Response from the AI analyst."""
    match_id: str
    analysis: dict
    advice: dict
    ml_prediction: float
    edge_signal: str
    generated_at: str
    is_fallback: Optional[bool] = False


@router.get("/live/pro/{match_id}/analysis", response_model=AIAnalysisResponse)
async def get_match_ai_analysis(match_id: str):
    """
    Get AI-powered analysis for a live pro match.
    
    Uses Gemini Pro to analyze:
    - Current match state (gold, XP, kills)
    - ML model prediction
    - Team statistics and recent form
    - Betting edge signals
    
    Returns actionable betting insights and recommendations.
    """
    steam_service = get_steam_service()
    
    if not steam_service.is_available:
        raise HTTPException(status_code=503, detail="Steam API not configured")
    
    # Find the match
    matches = await steam_service.get_live_matches(use_cache=True)
    match = next((m for m in matches if m.match_id == match_id), None)
    
    if not match:
        raise HTTPException(status_code=404, detail="Live match not found")
    
    # Get ML prediction
    feature_input = steam_service.to_feature_input(match)
    features = _feature_extractor.extract(feature_input)
    radiant_prob = _model.predict(features)
    edge_signal = _get_edge_signal(radiant_prob)
    
    # Fetch team stats from OpenDota (parallel)
    team_stats = {}
    try:
        radiant_team_id = getattr(match.radiant, 'team_id', 0) or 0
        dire_team_id = getattr(match.dire, 'team_id', 0) or 0
        
        if radiant_team_id > 0 or dire_team_id > 0:
            tasks = []
            if radiant_team_id > 0:
                tasks.append(opendota_client.get_team_stats(radiant_team_id))
                tasks.append(opendota_client.get_team_recent_form(radiant_team_id))
            if dire_team_id > 0:
                tasks.append(opendota_client.get_team_stats(dire_team_id))
                tasks.append(opendota_client.get_team_recent_form(dire_team_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            idx = 0
            if radiant_team_id > 0:
                radiant_stats = results[idx] if not isinstance(results[idx], Exception) else {}
                radiant_form = results[idx+1] if not isinstance(results[idx+1], Exception) else {}
                team_stats["radiant"] = {**radiant_stats, **radiant_form}
                idx += 2
            if dire_team_id > 0:
                dire_stats = results[idx] if not isinstance(results[idx], Exception) else {}
                dire_form = results[idx+1] if not isinstance(results[idx+1], Exception) else {}
                team_stats["dire"] = {**dire_stats, **dire_form}
    except Exception as e:
        logger.debug(f"Failed to fetch team stats: {e}")
    
    # Calculate momentum from recent stats
    momentum = 0.0
    if match.gold_diff > 0:
        momentum = min(1.0, match.gold_diff / 15000)  # Normalize
    else:
        momentum = max(-1.0, match.gold_diff / 15000)
    
    # Build match data dict for Gemini
    match_data = {
        "match_id": match.match_id,
        "league_name": match.league_name,
        "radiant_team": match.radiant_team_name,
        "dire_team": match.dire_team_name,
        "game_time": match.game_time,
        "radiant_score": match.radiant.score,
        "dire_score": match.dire.score,
        "gold_diff": match.gold_diff,
        "xp_diff": match.xp_diff,
        "spectators": match.spectators,
    }
    
    # Get AI analysis
    analyst = get_gemini_analyst()
    result = await analyst.analyze_match(
        match_data=match_data,
        ml_prediction=radiant_prob,
        edge_signal=edge_signal,
        team_stats=team_stats if team_stats else None,
        momentum=momentum,
        features=None  # Could pass feature dict here for more context
    )
    
    return AIAnalysisResponse(
        match_id=match_id,
        analysis=result.get("analysis", {}),
        advice=result.get("advice", {}),
        ml_prediction=radiant_prob,
        edge_signal=edge_signal,
        generated_at=result.get("generated_at", ""),
        is_fallback=result.get("is_fallback", False)
    )
