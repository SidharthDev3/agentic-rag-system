from fastapi import APIRouter, Depends
from app.api.deps import get_chunk_repo, get_document_repo, get_log_repo
from app.core.config import settings
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.repositories.log_repo import LogRepository
from app.schemas.stats import RecentQueryItem, StrategyCount, SystemStatsResponse

router = APIRouter(tags=["Observability & System"])


@router.get("/health")
async def health_check():
    """Health check endpoint indicating service availability and active engine."""
    return {
        "status": "healthy",
        "service": "NexusRAG API",
        "version": settings.VERSION,
        "database": "postgresql+pgvector" if settings.is_postgres else "sqlite",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "reranker_model": settings.RERANKER_MODEL,
    }


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    doc_repo: DocumentRepository = Depends(get_document_repo),
    chunk_repo: ChunkRepository = Depends(get_chunk_repo),
    log_repo: LogRepository = Depends(get_log_repo),
):
    """Retrieve telemetry metrics and aggregated system health statistics."""
    doc_count = await doc_repo.count()
    chunk_count = await chunk_repo.count()
    telemetry = await log_repo.get_stats()
    recent_logs = await log_repo.list_recent_logs(limit=10)

    recent_queries = [
        RecentQueryItem(
            id=l.id,
            query=l.query,
            strategy=l.strategy,
            retrieval_latency_ms=l.retrieval_latency_ms,
            rerank_latency_ms=l.rerank_latency_ms,
            total_latency_ms=l.total_latency_ms,
            chunk_count=len(l.retrieved_chunk_ids),
            created_at=l.created_at,
        )
        for l in recent_logs
    ]

    strategies = [
        StrategyCount(strategy=s["strategy"], count=s["count"])
        for s in telemetry.get("strategies", [])
    ]

    return SystemStatsResponse(
        document_count=doc_count,
        indexed_chunks_count=chunk_count,
        total_queries=telemetry.get("total_queries", 0),
        avg_latency_ms=telemetry.get("avg_latency_ms", 0.0),
        avg_retrieval_latency_ms=telemetry.get("avg_retrieval_latency_ms", 0.0),
        avg_llm_latency_ms=telemetry.get("avg_llm_latency_ms", 0.0),
        vector_store_status="connected (pgvector)" if settings.is_postgres else "active (local-vector)",
        reranker_status="active",
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        recent_queries=recent_queries,
        strategy_distribution=strategies,
    )

