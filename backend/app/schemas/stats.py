from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecentQueryItem(BaseModel):
    id: str
    query: str
    strategy: str
    retrieval_latency_ms: float
    rerank_latency_ms: float
    total_latency_ms: float
    chunk_count: int
    created_at: datetime


class StrategyCount(BaseModel):
    strategy: str
    count: int


class SystemStatsResponse(BaseModel):
    document_count: int
    indexed_chunks_count: int
    total_queries: int
    avg_latency_ms: float
    avg_retrieval_latency_ms: float
    avg_llm_latency_ms: float
    vector_store_status: str
    reranker_status: str
    llm_provider: str
    embedding_model: str
    recent_queries: List[RecentQueryItem] = Field(default_factory=list)
    strategy_distribution: List[StrategyCount] = Field(default_factory=list)

