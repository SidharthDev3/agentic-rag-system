from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: str  # e.g. "1" or "[1]"
    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_id: str
    relevance_score: float = 0.0
    text: str


class WorkflowStep(BaseModel):
    step: str
    name: str
    status: str = "completed"  # pending, running, completed, skipped, failed
    latency_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class LatencyBreakdown(BaseModel):
    query_analysis_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_generation_ms: float = 0.0
    verification_ms: float = 0.0
    total_ms: float = 0.0


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or instruction")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID if continuing a thread")
    top_k: Optional[int] = Field(5, ge=1, le=20)
    use_reranker: Optional[bool] = Field(True)
    strategy_override: Optional[str] = Field(None, description="Optional manual retrieval strategy override")


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    conversation_id: str
    message_id: str
    routing_strategy: str
    grounding_score: float = 1.0
    is_grounded: bool = True
    grounding_explanation: Optional[str] = None
    latency_breakdown: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    workflow_steps: List[WorkflowStep] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    document_ids: Optional[List[str]] = None
    use_reranking: bool = True


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: Optional[int] = None
    content: str
    score: float
    retrieval_type: str  # "vector", "keyword", "hybrid_rrf", "reranked"


class SearchResponse(BaseModel):
    query: str
    total_results: int
    latency_ms: float
    results: List[SearchResultItem]

