"""
API Rate Limit Tracker: Protects free tier quotas.

Tracks usage for:
- OpenDota: 50,000/month (no key) or 60/min with key
- PandaScore: 1,000/month
- Stratz: 10,000/month

Persists counts to file for cross-session tracking.
"""
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict
from loguru import logger


@dataclass
class APIQuota:
    """Quota configuration for an API."""
    name: str
    monthly_limit: int
    daily_limit: Optional[int] = None
    minute_limit: Optional[int] = None


# API Configurations
API_QUOTAS = {
    "opendota": APIQuota(
        name="OpenDota",
        monthly_limit=50000,
        daily_limit=1667,  # ~50k/30 days
        minute_limit=60
    ),
    "pandascore": APIQuota(
        name="PandaScore", 
        monthly_limit=1000,
        daily_limit=33
    ),
    "stratz": APIQuota(
        name="Stratz",
        monthly_limit=10000,
        daily_limit=333
    ),
}


@dataclass
class UsageStats:
    """Usage statistics for an API."""
    total_calls: int = 0
    daily_calls: Dict[str, int] = field(default_factory=dict)
    last_call: Optional[str] = None
    last_minute_calls: int = 0
    last_minute_timestamp: Optional[str] = None


class RateLimitTracker:
    """
    Tracks API usage across sessions.
    
    Features:
    - Persistent storage (survives restarts)
    - Daily/monthly/minute tracking
    - Warning thresholds (80%, 95%)
    - Blocking at limit
    """
    
    DATA_FILE = Path("data/rate_limits.json")
    WARNING_THRESHOLD = 0.80
    BLOCK_THRESHOLD = 0.95
    
    def __init__(self):
        self._usage: Dict[str, UsageStats] = {}
        self._load()
    
    def _load(self):
        """Load usage data from file."""
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if self.DATA_FILE.exists():
            try:
                with open(self.DATA_FILE, "r") as f:
                    data = json.load(f)
                    for api, stats in data.items():
                        self._usage[api] = UsageStats(**stats)
            except Exception as e:
                logger.warning(f"Failed to load rate limits: {e}")
        
        # Initialize missing APIs
        for api in API_QUOTAS:
            if api not in self._usage:
                self._usage[api] = UsageStats()
    
    def _save(self):
        """Save usage data to file."""
        try:
            data = {api: asdict(stats) for api, stats in self._usage.items()}
            with open(self.DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save rate limits: {e}")
    
    def can_call(self, api: str) -> bool:
        """
        Check if an API call is allowed.
        
        Returns False if:
        - Monthly quota at 95%+
        - Daily quota at 95%+
        - Minute quota exceeded (OpenDota)
        """
        if api not in API_QUOTAS:
            return True
        
        quota = API_QUOTAS[api]
        stats = self._usage.get(api, UsageStats())
        today = date.today().isoformat()
        
        # Check monthly
        if stats.total_calls >= quota.monthly_limit * self.BLOCK_THRESHOLD:
            logger.error(f"🚫 {quota.name} BLOCKED: Monthly limit reached ({stats.total_calls}/{quota.monthly_limit})")
            return False
        
        # Check daily
        daily_calls = stats.daily_calls.get(today, 0)
        if quota.daily_limit and daily_calls >= quota.daily_limit * self.BLOCK_THRESHOLD:
            logger.error(f"🚫 {quota.name} BLOCKED: Daily limit reached ({daily_calls}/{quota.daily_limit})")
            return False
        
        # Check minute (for OpenDota)
        if quota.minute_limit:
            now = datetime.utcnow()
            if stats.last_minute_timestamp:
                last_min = datetime.fromisoformat(stats.last_minute_timestamp)
                if (now - last_min).total_seconds() < 60:
                    if stats.last_minute_calls >= quota.minute_limit:
                        logger.warning(f"⏳ {quota.name}: Minute limit reached, wait...")
                        return False
        
        return True
    
    def record_call(self, api: str):
        """Record an API call."""
        if api not in self._usage:
            self._usage[api] = UsageStats()
        
        stats = self._usage[api]
        now = datetime.utcnow()
        today = date.today().isoformat()
        
        # Update totals
        stats.total_calls += 1
        stats.last_call = now.isoformat()
        
        # Update daily
        if today not in stats.daily_calls:
            stats.daily_calls[today] = 0
        stats.daily_calls[today] += 1
        
        # Update minute tracking
        if stats.last_minute_timestamp:
            last_min = datetime.fromisoformat(stats.last_minute_timestamp)
            if (now - last_min).total_seconds() >= 60:
                stats.last_minute_calls = 1
                stats.last_minute_timestamp = now.isoformat()
            else:
                stats.last_minute_calls += 1
        else:
            stats.last_minute_calls = 1
            stats.last_minute_timestamp = now.isoformat()
        
        # Check warnings
        self._check_warnings(api)
        
        # Save periodically (every 10 calls)
        if stats.total_calls % 10 == 0:
            self._save()
    
    def _check_warnings(self, api: str):
        """Log warnings at threshold."""
        if api not in API_QUOTAS:
            return
            
        quota = API_QUOTAS[api]
        stats = self._usage[api]
        today = date.today().isoformat()
        
        # Monthly warning
        usage_pct = stats.total_calls / quota.monthly_limit
        if usage_pct >= self.WARNING_THRESHOLD:
            logger.warning(f"⚠️ {quota.name}: {usage_pct:.0%} of monthly quota used!")
        
        # Daily warning
        daily_calls = stats.daily_calls.get(today, 0)
        if quota.daily_limit:
            daily_pct = daily_calls / quota.daily_limit
            if daily_pct >= self.WARNING_THRESHOLD:
                logger.warning(f"⚠️ {quota.name}: {daily_pct:.0%} of daily quota used!")
    
    def status(self) -> Dict[str, Dict]:
        """Get current usage status for all APIs."""
        result = {}
        today = date.today().isoformat()
        
        for api, quota in API_QUOTAS.items():
            stats = self._usage.get(api, UsageStats())
            daily_calls = stats.daily_calls.get(today, 0)
            
            result[api] = {
                "name": quota.name,
                "monthly_used": stats.total_calls,
                "monthly_limit": quota.monthly_limit,
                "monthly_pct": f"{stats.total_calls / quota.monthly_limit:.1%}",
                "daily_used": daily_calls,
                "daily_limit": quota.daily_limit,
                "last_call": stats.last_call,
                "can_call": self.can_call(api),
            }
        
        return result
    
    def reset_monthly(self):
        """Reset monthly counters (call on month change)."""
        for stats in self._usage.values():
            stats.total_calls = 0
        self._save()
        logger.info("🔄 Monthly rate limits reset")
    
    def reset_daily(self, api: Optional[str] = None):
        """Reset daily counters."""
        today = date.today().isoformat()
        
        if api:
            if api in self._usage:
                self._usage[api].daily_calls[today] = 0
        else:
            for stats in self._usage.values():
                stats.daily_calls[today] = 0
        
        self._save()


# Singleton instance
tracker = RateLimitTracker()
