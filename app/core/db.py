from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from loguru import logger
import os

# Use env var directly or from config if available. 
# Assuming DATABASE_URL is set in environment.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/dbname")

engine = None
_db_connected = False

try:
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
except Exception as e:
    logger.warning(f"Failed to create DB engine: {e}")

async def get_session() -> AsyncSession:
    if not engine:
        raise RuntimeError("Database not available")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

async def init_db():
    global _db_connected
    if not engine:
        logger.warning("Skipping DB init - no engine")
        return
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        _db_connected = True
        logger.info("Database connected and tables created")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running without DB.")
        _db_connected = False

async def connect_db():
    await init_db()

async def disconnect_db():
    if engine:
        await engine.dispose()

def is_db_connected() -> bool:
    return _db_connected

