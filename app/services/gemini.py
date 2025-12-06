"""
Gemini AI Analyst: Provides AI-powered match analysis using Google's Gemini Pro.

Deeply integrated with the Chronosphere system to provide:
- Comprehensive betting analysis with full context
- Actionable betting recommendations
- Natural language explanations of predictions
"""
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import json

from app.core.config import settings


@dataclass
class MatchAnalysis:
    """Structured AI analysis of a match."""
    summary: str                    # "Radiant has a commanding lead..."
    key_factors: List[str]          # ["Gold lead of 8k", "Radiant carry 6-0"]
    risk_level: str                 # "LOW", "MEDIUM", "HIGH"
    confidence_reasoning: str       # "High confidence due to..."
    momentum_analysis: str          # "Dire winning recent fights..."
    betting_insight: str            # "Consider Radiant at these odds..."


@dataclass
class BettingAdvice:
    """Actionable betting recommendation."""
    recommendation: str             # "STRONG_BET", "SMALL_BET", "SKIP"
    suggested_side: str             # "RADIANT", "DIRE", "NONE"
    reasoning: str                  # "The 15% edge on Radiant..."
    stake_suggestion: str           # "1-2% of bankroll"
    warnings: List[str]             # ["Late game carry could turn it"]


class GeminiAnalyst:
    """
    AI-powered match analyst using Google's Gemini Pro.
    
    Integrates with all system data for accurate, contextual analysis:
    - ML model predictions
    - Edge signals
    - Live match stats
    - Team history from OpenDota
    - Momentum indicators
    """
    
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    # System prompt for betting analysis
    SYSTEM_PROMPT = """You are an expert Dota 2 match analyst for a professional betting platform called Chronosphere.

Your role is to analyze live matches and provide actionable betting insights. You have access to:
- Real-time match data from Steam API
- ML model predictions with probability estimates
- Team statistics and recent form from OpenDota
- Betting edge calculations

Guidelines:
1. Be CONCISE but insightful - bettors need quick, actionable information
2. Focus on VALUE - identify when odds are mispriced
3. Highlight KEY FACTORS that will determine the match outcome
4. Be honest about uncertainty - Dota 2 is volatile
5. Consider game tempo, draft, and player form
6. Never guarantee outcomes - provide probability-based reasoning

Format your response as JSON with this structure:
{
    "summary": "Brief 1-2 sentence match summary",
    "key_factors": ["Factor 1", "Factor 2", "Factor 3"],
    "risk_level": "LOW|MEDIUM|HIGH",
    "confidence_reasoning": "Why we're confident or not",
    "momentum_analysis": "Who's controlling the game pace",
    "betting_insight": "Actionable betting advice",
    "recommendation": "STRONG_BET|SMALL_BET|SKIP",
    "suggested_side": "RADIANT|DIRE|NONE",
    "reasoning": "Detailed reasoning for the recommendation",
    "stake_suggestion": "Suggested stake as % of bankroll",
    "warnings": ["Risk factor 1", "Risk factor 2"]
}"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
    
    @property
    def is_available(self) -> bool:
        """Check if Gemini API is configured."""
        return bool(self.api_key)
    
    async def analyze_match(
        self,
        match_data: Dict[str, Any],
        ml_prediction: float,
        edge_signal: str,
        team_stats: Optional[Dict[str, Any]] = None,
        momentum: float = 0.0,
        features: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive match analysis using Gemini.
        
        Args:
            match_data: Live match data (from LiveProMatch)
            ml_prediction: Radiant win probability from ML model
            edge_signal: "RADIANT_VALUE", "DIRE_VALUE", or "NO_EDGE"
            team_stats: Optional team history from OpenDota
            momentum: Momentum score (-1 to 1, positive = Radiant momentum)
            features: Optional feature dict for context
        
        Returns:
            Dict with MatchAnalysis and BettingAdvice fields
        """
        if not self.is_available:
            return self._fallback_analysis(match_data, ml_prediction, edge_signal)
        
        # Build context prompt
        context = self._build_context(
            match_data, ml_prediction, edge_signal, team_stats, momentum, features
        )
        
        try:
            response = await self._call_gemini(context)
            return self._parse_response(response, match_data, ml_prediction, edge_signal)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return self._fallback_analysis(match_data, ml_prediction, edge_signal)
    
    def _build_context(
        self,
        match_data: Dict[str, Any],
        ml_prediction: float,
        edge_signal: str,
        team_stats: Optional[Dict[str, Any]],
        momentum: float,
        features: Optional[Dict[str, float]]
    ) -> str:
        """Build the context prompt for Gemini."""
        
        # Extract key match info
        radiant = match_data.get("radiant_team", "Radiant")
        dire = match_data.get("dire_team", "Dire")
        game_time = match_data.get("game_time", 0)
        game_time_mins = game_time // 60
        gold_diff = match_data.get("gold_diff", 0)
        xp_diff = match_data.get("xp_diff", 0)
        radiant_score = match_data.get("radiant_score", 0)
        dire_score = match_data.get("dire_score", 0)
        spectators = match_data.get("spectators", 0)
        league = match_data.get("league_name", "Unknown League")
        
        # ML Model context
        radiant_prob = ml_prediction
        dire_prob = 1 - ml_prediction
        confidence = "HIGH" if abs(radiant_prob - 0.5) > 0.2 else "MEDIUM" if abs(radiant_prob - 0.5) > 0.1 else "LOW"
        
        # Build prompt
        prompt = f"""Analyze this live Dota 2 match:

## Match Info
- **League**: {league}
- **{radiant}** (Radiant) vs **{dire}** (Dire)
- **Game Time**: {game_time_mins} minutes
- **Spectators**: {spectators:,}

## Live Stats
- **Score**: {radiant_score} - {dire_score}
- **Gold Difference**: {gold_diff:+,} (positive = Radiant ahead)
- **XP Difference**: {xp_diff:+,}

## ML Model Prediction
- **Radiant Win Probability**: {radiant_prob:.1%}
- **Dire Win Probability**: {dire_prob:.1%}
- **Model Confidence**: {confidence}

## Edge Signal
- **Current Signal**: {edge_signal}
- **Momentum**: {momentum:+.2f} (-1 = Dire momentum, +1 = Radiant momentum)

"""
        
        # Add team stats if available
        if team_stats:
            radiant_stats = team_stats.get("radiant", {})
            dire_stats = team_stats.get("dire", {})
            
            if radiant_stats or dire_stats:
                prompt += "## Team Form\n"
                if radiant_stats:
                    wr = radiant_stats.get("win_rate", 0.5)
                    recent_wr = radiant_stats.get("recent_win_rate", 0.5)
                    prompt += f"- **{radiant}**: {wr:.1%} overall win rate, {recent_wr:.1%} recent form\n"
                if dire_stats:
                    wr = dire_stats.get("win_rate", 0.5)
                    recent_wr = dire_stats.get("recent_win_rate", 0.5)
                    prompt += f"- **{dire}**: {wr:.1%} overall win rate, {recent_wr:.1%} recent form\n"
                prompt += "\n"
        
        # Add feature context if available
        if features:
            prompt += "## Advanced Features\n"
            if "networth_gini" in features:
                gini = features["networth_gini"]
                prompt += f"- **Gold Distribution**: {'Concentrated' if gini > 0.3 else 'Distributed'} (Gini: {gini:.2f})\n"
            if "carry_efficiency_index" in features:
                cei = features["carry_efficiency_index"]
                prompt += f"- **Carry Efficiency**: {cei:.2f}x benchmark\n"
            prompt += "\n"
        
        prompt += "Provide your analysis in the JSON format specified."
        
        return prompt
    
    async def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API with the prompt."""
        url = f"{self.GEMINI_API_URL}?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self.SYSTEM_PROMPT},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract text from response
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            raise
    
    def _parse_response(
        self,
        response: Dict[str, Any],
        match_data: Dict[str, Any],
        ml_prediction: float,
        edge_signal: str
    ) -> Dict[str, Any]:
        """Parse and validate Gemini response."""
        
        # Create MatchAnalysis
        analysis = MatchAnalysis(
            summary=response.get("summary", "Analysis unavailable"),
            key_factors=response.get("key_factors", []),
            risk_level=response.get("risk_level", "MEDIUM"),
            confidence_reasoning=response.get("confidence_reasoning", ""),
            momentum_analysis=response.get("momentum_analysis", ""),
            betting_insight=response.get("betting_insight", "")
        )
        
        # Create BettingAdvice
        advice = BettingAdvice(
            recommendation=response.get("recommendation", "SKIP"),
            suggested_side=response.get("suggested_side", "NONE"),
            reasoning=response.get("reasoning", ""),
            stake_suggestion=response.get("stake_suggestion", "0%"),
            warnings=response.get("warnings", [])
        )
        
        return {
            "analysis": asdict(analysis),
            "advice": asdict(advice),
            "match_id": match_data.get("match_id"),
            "generated_at": datetime.utcnow().isoformat(),
            "ml_prediction": ml_prediction,
            "edge_signal": edge_signal
        }
    
    def _fallback_analysis(
        self,
        match_data: Dict[str, Any],
        ml_prediction: float,
        edge_signal: str
    ) -> Dict[str, Any]:
        """Provide rule-based analysis when Gemini is unavailable."""
        
        radiant = match_data.get("radiant_team", "Radiant")
        dire = match_data.get("dire_team", "Dire")
        gold_diff = match_data.get("gold_diff", 0)
        
        # Determine leading team
        if ml_prediction > 0.55:
            leader = radiant
            prob = ml_prediction
        elif ml_prediction < 0.45:
            leader = dire
            prob = 1 - ml_prediction
        else:
            leader = "Neither team"
            prob = 0.5
        
        # Generate summary
        if abs(gold_diff) > 10000:
            summary = f"{leader} has a commanding lead with {abs(gold_diff):,} gold advantage."
        elif abs(gold_diff) > 5000:
            summary = f"{leader} has a solid lead but the game is still contestable."
        else:
            summary = "This is a close game with either team capable of winning."
        
        # Determine recommendation
        if edge_signal == "RADIANT_VALUE" and ml_prediction > 0.55:
            recommendation = "SMALL_BET"
            suggested_side = "RADIANT"
        elif edge_signal == "DIRE_VALUE" and ml_prediction < 0.45:
            recommendation = "SMALL_BET"
            suggested_side = "DIRE"
        else:
            recommendation = "SKIP"
            suggested_side = "NONE"
        
        analysis = MatchAnalysis(
            summary=summary,
            key_factors=[
                f"Gold difference: {gold_diff:+,}",
                f"ML prediction: {radiant} {ml_prediction:.1%}"
            ],
            risk_level="MEDIUM",
            confidence_reasoning="Rule-based analysis (AI unavailable)",
            momentum_analysis="Unable to assess momentum without AI",
            betting_insight=f"Edge signal indicates {edge_signal}"
        )
        
        advice = BettingAdvice(
            recommendation=recommendation,
            suggested_side=suggested_side,
            reasoning=f"Based on ML model probability of {ml_prediction:.1%} for {radiant}",
            stake_suggestion="1% or less" if recommendation == "SMALL_BET" else "0%",
            warnings=["AI analysis unavailable - using fallback rules"]
        )
        
        return {
            "analysis": asdict(analysis),
            "advice": asdict(advice),
            "match_id": match_data.get("match_id"),
            "generated_at": datetime.utcnow().isoformat(),
            "ml_prediction": ml_prediction,
            "edge_signal": edge_signal,
            "is_fallback": True
        }


# Lazy singleton
_gemini_analyst_instance: Optional[GeminiAnalyst] = None

def get_gemini_analyst() -> GeminiAnalyst:
    """Get the Gemini analyst singleton."""
    global _gemini_analyst_instance
    if _gemini_analyst_instance is None:
        _gemini_analyst_instance = GeminiAnalyst()
    return _gemini_analyst_instance

class _GeminiAnalystProxy:
    """Proxy for lazy initialization."""
    def __getattr__(self, name):
        return getattr(get_gemini_analyst(), name)

gemini_analyst = _GeminiAnalystProxy()
