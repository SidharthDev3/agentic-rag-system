from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: str, load_chunks: bool = False) -> Optional[Document]:
        query = select(Document).where(Document.id == document_id)
        if load_chunks:
            query = query.options(selectinload(Document.chunks))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_hash(self, content_hash: str) -> Optional[Document]:
        query = select(Document).where(Document.content_hash == content_hash)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_documents(
        self, skip: int = 0, limit: int = 50, status: Optional[str] = None
    ) -> tuple[List[Document], int]:
        query = select(Document)
        if status:
            query = query.where(Document.status == status)
        query = query.order_by(Document.created_at.desc())

        # Total count
        count_query = select(func.count(Document.id))
        if status:
            count_query = count_query.where(Document.status == status)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def create(self, document: Document) -> Document:
        self.db.add(document)
        await self.db.flush()
        return document

    async def update_status(
        self, document_id: str, status: str, chunk_count: int = 0, error_message: Optional[str] = None
    ) -> Optional[Document]:
        doc = await self.get_by_id(document_id)
        if doc:
            doc.status = status
            doc.chunk_count = chunk_count
            doc.error_message = error_message
            await self.db.flush()
        return doc

    async def delete(self, document_id: str) -> bool:
        doc = await self.get_by_id(document_id)
        if doc:
            await self.db.delete(doc)
            await self.db.flush()
            return True
        return False

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Document.id)))
        return result.scalar() or 0

