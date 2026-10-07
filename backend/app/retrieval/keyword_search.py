import math
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.models.chunk import DocumentChunk
from app.models.document import Document


class KeywordSearcher:
    """Executes sparse keyword / full-text search against document chunks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        results = []

        if settings.is_postgres:
            try:
                # PostgreSQL Full-Text Search with ts_rank_cd
                sql = (
                    "SELECT c.id, c.document_id, c.chunk_index, c.content, c.page_number, "
                    "c.section, c.source, d.filename, "
                    "ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', :query)) as rank "
                    "FROM document_chunks c "
                    "JOIN documents d ON c.document_id = d.id "
                    "WHERE d.status = 'indexed' "
                    "AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query) "
                )
                params: Dict[str, Any] = {"query": query, "limit": top_k}
                if document_ids:
                    sql += "AND c.document_id = ANY(:doc_ids) "
                    params["doc_ids"] = document_ids
                sql += "ORDER BY rank DESC LIMIT :limit"

                res = await self.db.execute(text(sql), params)
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
                        "score": float(row[8]),
                        "retrieval_type": "keyword",
                    })
                return results
            except Exception as e:
                logger.warning(f"PostgreSQL FTS search failed ({e}). Falling back to lexical BM25 matching.")

        # Universal BM25 / token matching fallback
        q_terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 1]
        if not q_terms:
            return []

        q = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.status == "indexed")
        )
        if document_ids:
            q = q.where(DocumentChunk.document_id.in_(document_ids))

        res = await self.db.execute(q)
        all_chunks = res.all()
        if not all_chunks:
            return []

        doc_count = len(all_chunks)
        # Term frequencies across corpus
        df = {}
        for term in q_terms:
            df[term] = sum(1 for c, _ in all_chunks if term in c.content.lower())

        candidates = []
        for chunk, filename in all_chunks:
            text_lower = chunk.content.lower()
            tokens = re.findall(r"\w+", text_lower)
            doc_len = len(tokens)
            if doc_len == 0:
                continue

            score = 0.0
            for term in q_terms:
                if df[term] == 0:
                    continue
                tf = tokens.count(term)
                if tf > 0:
                    idf = math.log(1 + (doc_count - df[term] + 0.5) / (df[term] + 0.5))
                    # Simplified BM25 formula: k1=1.5, b=0.75
                    k1 = 1.5
                    b = 0.75
                    avg_dl = 200.0
                    term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_dl)))
                    score += term_score

            if score > 0:
                candidates.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "source": chunk.source,
                    "filename": filename,
                    "score": score,
                    "retrieval_type": "keyword",
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

