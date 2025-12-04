from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from datetime import datetime

class Match(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    provider_match_id: Optional[str] = Field(index=True) # ID from GSI
    start_time: datetime = Field(default_factory=datetime.utcnow)
    radiant_team: Optional[str] = None
    dire_team: Optional[str] = None
    winner: Optional[str] = None # "Radiant" or "Dire"

class Tick(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: UUID = Field(foreign_key="match.id", index=True)
    game_time: int = Field(index=True)
    win_probability: float
    radiant_gold_lead: int = 0
    radiant_xp_lead: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
