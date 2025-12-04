import asyncio
from typing import List, Dict, Any
from loguru import logger
from app.core.db import get_session
from app.models import Match, Tick
from sqlmodel import select
from datetime import datetime

class BatchWriter:
    def __init__(self, batch_size: int = 100, flush_interval: int = 5):
        self.buffer: List[Dict[str, Any]] = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.last_flush = datetime.utcnow()
        self._lock = asyncio.Lock()

    async def add_tick(self, tick_data: Dict[str, Any], win_prob: float):
        """
        Convert raw tick data + prediction into a Tick dictionary and add to buffer.
        """
        try:
            map_data = tick_data.get('map', {})
            # For now, we use a dummy match_id since we don't have full match management yet.
            # In a real scenario, we'd look up the active match ID.
            # We'll need to ensure at least one match exists in the DB to link to.
            
            # Note: SQLModel expects UUID object for UUID fields if defined as such, 
            # but usually handles strings if they are valid UUIDs. 
            # Our model defines id as UUID.
            # Let's use a fixed UUID for the dummy match.
            dummy_match_uuid = "00000000-0000-0000-0000-000000000000"

            tick = {
                "match_id": dummy_match_uuid, 
                "game_time": map_data.get('clock_time', 0),
                "win_probability": win_prob,
                "radiant_gold_lead": 0, # Extract from features if available
                "radiant_xp_lead": 0,   # Extract from features if available
            }
            
            async with self._lock:
                self.buffer.append(tick)
            
            if len(self.buffer) >= self.batch_size or (datetime.utcnow() - self.last_flush).total_seconds() > self.flush_interval:
                await self.flush()
                
        except Exception as e:
            logger.error(f"Error adding tick to batch: {e}")

    async def flush(self):
        async with self._lock:
            if not self.buffer:
                return
            
            ticks_to_save_data = list(self.buffer)
            self.buffer.clear()
            self.last_flush = datetime.utcnow()

        try:
            logger.info(f"Flushing {len(ticks_to_save_data)} ticks to DB...")
            
            dummy_match_uuid = "00000000-0000-0000-0000-000000000000"

            async for session in get_session():
                # Ensure dummy match exists (hack for now)
                statement = select(Match).where(Match.id == dummy_match_uuid)
                results = await session.exec(statement)
                match = results.first()
                
                if not match:
                    match = Match(
                        id=dummy_match_uuid,
                        provider_match_id='12345',
                        radiant_team='Radiant',
                        dire_team='Dire'
                    )
                    session.add(match)
                    await session.commit()

                # Bulk create ticks
                # SQLModel doesn't have a direct bulk_create in the session API like Prisma
                # We can use session.add_all with model instances
                ticks = [Tick(**data) for data in ticks_to_save_data]
                session.add_all(ticks)
                await session.commit()
                
            logger.info("Flush complete.")
                
        except Exception as e:
            logger.error(f"Error flushing to DB: {e}")

