import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from ..models.schema import Base

# Handle database URL with support for MAIN_DB_PATH
main_db_path = os.getenv("MAIN_DB_PATH")
if main_db_path:
    DATABASE_URL = f"sqlite:///{main_db_path}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../telequery_db/telegram_messages.db")
ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Synchronous engine for initial setup
sync_engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Asynchronous engine for FastAPI
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=sync_engine)


async def get_async_session():
    """Get async database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()