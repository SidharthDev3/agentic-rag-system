from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import DocumentChunk


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_many(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        self.db.add_all(chunks)
        await self.db.flush()
        return chunks

    async def get_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        result = await self.db.execute(select(DocumentChunk).where(DocumentChunk.id == chunk_id))
        return result.scalar_one_or_none()

    async def get_by_ids(self, chunk_ids: List[str]) -> List[DocumentChunk]:
        if not chunk_ids:
            return []
        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
        )
        return list(result.scalars().all())

    async def list_by_document(
        self, document_id: str, skip: int = 0, limit: int = 100
    ) -> List[DocumentChunk]:
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_by_document(self, document_id: str) -> int:
        result = await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await self.db.flush()
        return result.rowcount

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(DocumentChunk.id)))
        return result.scalar() or 0

