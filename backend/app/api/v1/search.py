import asyncio
import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.retrieval.cross_encoder_reranker import CrossEncoderReranker
from app.retrieval.hybrid_fusion import HybridFusion
from app.retrieval.keyword_search import KeywordSearcher
from app.retrieval.vector_search import VectorSearcher
from app.schemas.chat import SearchRequest, SearchResponse, SearchResultItem
from app.services.embedding_service import embedding_service

router = APIRouter(prefix="/search", tags=["Retrieval Search"])


@router.post("", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Direct hybrid search endpoint (Dense Vector + Full-Text Keyword + RRF Fusion + Reranking).
    Useful for inspecting retrieval quality and raw chunk matching scores.
    """
    start_time = time.perf_counter()

    q_vec = await embedding_service.get_embedding(payload.query)
    vector_searcher = VectorSearcher(db)
    keyword_searcher = KeywordSearcher(db)

    dense_results = await vector_searcher.search(
        query_vector=q_vec,
        top_k=payload.top_k * 2,
        document_ids=payload.document_ids,
    )
    sparse_results = await keyword_searcher.search(
        query=payload.query,
        top_k=payload.top_k * 2,
        document_ids=payload.document_ids,
    )

    fused = HybridFusion.fuse(
        dense_results=dense_results,
        sparse_results=sparse_results,
        top_k=payload.top_k * 2,
    )

    if payload.use_reranking and fused:
        reranker = CrossEncoderReranker(top_k=payload.top_k)
        final_results = await reranker.rerank(
            query=payload.query, candidates=fused, top_k=payload.top_k
        )
    else:
        final_results = fused[: payload.top_k]

    latency_ms = (time.perf_counter() - start_time) * 1000

    items = [
        SearchResultItem(
            chunk_id=c.get("chunk_id", ""),
            document_id=c.get("document_id", ""),
            filename=c.get("filename", "unknown"),
            page=c.get("page_number", 1),
            content=c.get("content", ""),
            score=round(float(c.get("rerank_score", c.get("score", 0.0))), 3),
            retrieval_type=c.get("retrieval_type", "hybrid"),
        )
        for c in final_results
    ]

    return SearchResponse(
        query=payload.query,
        total_results=len(items),
        latency_ms=round(latency_ms, 2),
        results=items,
    )
