from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Get the project root directory (parent of app/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra env vars like FRONTEND_PORT, POSTGRES_*
    )
    
    # Security
    ALLOWED_IPS: list[str] = ["127.0.0.1", "::1"]
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # Environment
    ENV: str = "dev"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chronosphere"
    
    # API Keys (External Services)
    OPENDOTA_API_KEY: Optional[str] = None  # Optional for free tier
    PANDASCORE_API_KEY: Optional[str] = None  # Required for production
    STRATZ_API_KEY: Optional[str] = None  # Required for context
    STEAM_API_KEY: Optional[str] = None  # Required for live pro matches
    GEMINI_API_KEY: Optional[str] = None  # For AI analyst feature
    
    # Mock Mode (Development)
    USE_MOCK_ODDS: bool = True  # Set to False in production
    USE_MOCK_CONTEXT: bool = True  # Set to False in production
    
    # Polling Intervals (seconds)
    MARKET_POLL_INTERVAL_PREGAME: int = 60
    MARKET_POLL_INTERVAL_INGAME: int = 30

settings = Settings()



