from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os

# Use env var directly or from config if available. 
# Assuming DATABASE_URL is set in environment.
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/dbname")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def connect_db():
    await init_db()

async def disconnect_db():
    await engine.dispose()
