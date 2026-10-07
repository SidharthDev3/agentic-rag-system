import asyncio
import time
from typing import Any, Dict, List
from app.agents.state import AgentState
from app.db.session import async_session_factory
from app.retrieval.hybrid_fusion import HybridFusion
from app.retrieval.keyword_search import KeywordSearcher
from app.retrieval.vector_search import VectorSearcher
from app.schemas.chat import WorkflowStep
from app.services.embedding_service import embedding_service


async def hybrid_retriever_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    queries = state.get("rewritten_queries", [state["query"]])
    strategy = state.get("retrieval_strategy", "single_hop_hybrid")

    all_dense_results: List[Dict[str, Any]] = []
    all_sparse_results: List[Dict[str, Any]] = []

    async with async_session_factory() as session:
        vector_searcher = VectorSearcher(session)
        keyword_searcher = KeywordSearcher(session)

        # Retrieve for each query variant
        for q in queries[:2]:  # Top 2 search queries
            q_vec = await embedding_service.get_embedding(q)

            dense_res = await vector_searcher.search(query_vector=q_vec, top_k=10)
            sparse_res = await keyword_searcher.search(query=q, top_k=10)
            all_dense_results.extend(dense_res)
            all_sparse_results.extend(sparse_res)

    # Reciprocal Rank Fusion (RRF)
    fused_chunks = HybridFusion.fuse(
        dense_results=all_dense_results,
        sparse_results=all_sparse_results,
        top_k=15,
    )

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="hybrid_retriever",
        name="Hybrid Dense & Sparse Search",
        status="completed",
        latency_ms=round(latency, 2),
        details={
            "strategy": strategy,
            "queries_executed": len(queries[:2]),
            "dense_count": len(all_dense_results),
            "sparse_count": len(all_sparse_results),
            "fused_count": len(fused_chunks),
        },
    )

    return {
        "retrieved_chunks": fused_chunks,
        "workflow_steps": state.get("workflow_steps", []) + [step],
        "retrieval_ms": round(latency, 2),
    }
