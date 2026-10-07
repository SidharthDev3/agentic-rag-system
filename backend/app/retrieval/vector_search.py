from typing import Any, Dict, List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.services.embedding_service import embedding_service


class VectorSearcher:
    """Executes dense semantic similarity search against document chunks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        results = []

        if settings.is_postgres:
            try:
                # Native pgvector cosine distance: embedding <=> :vector
                query_str = (
                    "SELECT c.id, c.document_id, c.chunk_index, c.content, c.page_number, "
                    "c.section, c.source, d.filename, (1 - (c.embedding <=> :vector::vector)) as score "
                    "FROM document_chunks c "
                    "JOIN documents d ON c.document_id = d.id "
                    "WHERE d.status = 'indexed' "
                )
                params: Dict[str, Any] = {"vector": str(query_vector), "limit": top_k}
                if document_ids:
                    query_str += "AND c.document_id = ANY(:doc_ids) "
                    params["doc_ids"] = document_ids
                query_str += "ORDER BY c.embedding <=> :vector::vector ASC LIMIT :limit"

                res = await self.db.execute(text(query_str), params)
                for row in res.fetchall():
                    results.append({
                        "chunk_id": str(row[0]),
                        "document_id": str(row[1]),
                        "chunk_index": row[2],
                        "content": row[3],
                        "page_number": row[4],
                        "section": row[5],
                        "source": row[6],
                        "filename": row[7],
                        "score": max(0.0, float(row[8])),
                        "retrieval_type": "vector",
                    })
                return results
            except Exception as e:
                logger.warning(f"Native pgvector search failed ({e}). Falling back to ORM similarity.")

        # Fallback ORM vector similarity (works universally including SQLite)
        query = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
        )
        if document_ids:
            query = query.where(DocumentChunk.document_id.in_(document_ids))

        res = await self.db.execute(query)
        candidates = []
        for chunk, filename in res.all():
            if chunk.embedding:
                sim = embedding_service.cosine_similarity(query_vector, chunk.embedding)
                candidates.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "source": chunk.source,
                    "filename": filename,
                    "score": sim,
                    "retrieval_type": "vector",
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

