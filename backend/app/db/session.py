from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger

database_url = settings.DATABASE_URL
if settings.is_postgres:
    try:
        import asyncpg  # noqa: F401
    except ImportError:
        logger.warning(
            "asyncpg driver is not installed in the local Python environment. "
            "Falling back to local SQLite: sqlite+aiosqlite:///./nexusrag.db. "
            "For full PostgreSQL + pgvector, use Docker Compose."
        )
        database_url = "sqlite+aiosqlite:///./nexusrag.db"

# Engine configuration
connect_args = {}
if "sqlite" in database_url.lower():
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    connect_args=connect_args,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
