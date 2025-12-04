from collections import deque
from typing import Dict, Any, Optional
from loguru import logger

class RingBuffer:
    def __init__(self, max_len: int = 30):
        """
        Initialize RingBuffer.
        Assuming 10 ticks/sec, 30 ticks = 3 seconds of history.
        """
        self.buffer = deque(maxlen=max_len)
        self.last_game_time = -1

    def add_tick(self, tick: Dict[str, Any]) -> bool:
        """
        Add a tick to the buffer.
        Returns True if the tick is new and valid, False if it's a duplicate.
        """
        try:
            map_data = tick.get('map', {})
            game_time = map_data.get('clock_time', -1)
            
            # Deduplication: If tick.game_time == last_tick.game_time, discard
            # In a real scenario, we might check order_id if available, but clock_time is a good proxy for now.
            if game_time == self.last_game_time:
                return False
            
            self.buffer.append(tick)
            self.last_game_time = game_time
            return True
        except Exception as e:
            logger.error(f"Error adding tick to buffer: {e}")
            return False

    def get_latest_tick(self) -> Optional[Dict[str, Any]]:
        if not self.buffer:
            return None
        return self.buffer[-1]

    def get_smoothed_features(self) -> Optional[Dict[str, Any]]:
        """
        Placeholder for feature smoothing logic.
        For now, returns the latest tick.
        In the future, this will average out gold/xp over the buffer.
        """
        return self.get_latest_tick()
