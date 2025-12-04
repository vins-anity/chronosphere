import asyncio
from typing import Optional

# Global queue for in-memory processing
# Initialized in main.py startup
queue: Optional[asyncio.Queue] = None
