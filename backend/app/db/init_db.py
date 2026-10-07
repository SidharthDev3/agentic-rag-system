from sqlalchemy import text
from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401


async def init_db() -> None:
    """Initialize database schemas, extensions, and tables."""
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        if settings.is_postgres:
            try:
                logger.info("Ensuring pgvector extension is enabled...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            except Exception as e:
                logger.warning("Could not create pgvector extension: %s", e)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Create PostgreSQL Full-Text Search GIN index if on postgres
        if settings.is_postgres:
            try:
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_chunks_content_fts "
                        "ON document_chunks USING gin(to_tsvector('english', content));"
                    )
                )
            except Exception as e:
                logger.warning("Could not create FTS GIN index: %s", e)

    logger.info("Database initialization completed successfully.")

