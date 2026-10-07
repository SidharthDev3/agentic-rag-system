from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from app.schemas.chat import Citation, WorkflowStep


class AgentState(TypedDict):
    # User Input
    query: str
    conversation_id: Optional[str]
    conversation_history: List[Dict[str, str]]
    top_k: int
    use_reranker: bool
    strategy_override: Optional[str]

    # Query Analysis & Routing
    classification: str  # factual, summarization, comparison, multi_doc, analytical, conversational
    needs_retrieval: bool
    entities: List[str]
    rewritten_queries: List[str]
    retrieval_strategy: str

    # Retrieval & Reranking
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    compressed_context: str

    # Generation & Citations
    raw_answer: str
    answer: str
    citations: List[Citation]

    # Evaluation & Grounding
    is_grounded: bool
    grounding_score: float
    grounding_explanation: Optional[str]

    # Telemetry & Workflow
    workflow_steps: List[WorkflowStep]
    query_analysis_ms: float
    retrieval_ms: float
    rerank_ms: float
    llm_generation_ms: float
    verification_ms: float
    total_latency_ms: float
    error: Optional[str]

