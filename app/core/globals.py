"""
Global state module for Chronosphere.

This module provides backward compatibility with the old queue-based system
while transitioning to the new StateManager-based architecture.
"""
import asyncio
from typing import Optional

# Legacy: Global queue for in-memory processing
# Initialized in main.py startup
queue: Optional[asyncio.Queue] = None

# New: Import StateManager singleton for the Lite Monolith architecture
from app.core.state import state_manager, StateManager
