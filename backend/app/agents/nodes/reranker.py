import time
from typing import Any, Dict
from app.agents.state import AgentState
from app.retrieval.cross_encoder_reranker import CrossEncoderReranker
from app.schemas.chat import WorkflowStep


async def reranker_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    candidates = state.get("retrieved_chunks", [])
    query = state["query"]
    top_k = state.get("top_k", 5)
    use_reranker = state.get("use_reranker", True)

    if not candidates:
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="reranker",
            name="Cross-Encoder Reranking",
            status="completed",
            latency_ms=round(latency, 2),
            details={"candidates_in": 0, "reranked_out": 0},
        )
        return {
            "reranked_chunks": [],
            "workflow_steps": state.get("workflow_steps", []) + [step],
            "rerank_ms": round(latency, 2),
        }

    if use_reranker:
        reranker = CrossEncoderReranker(top_k=top_k)
        reranked = await reranker.rerank(query=query, candidates=candidates, top_k=top_k)
    else:
        reranked = candidates[:top_k]

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="reranker",
        name="Cross-Encoder Reranking",
        status="completed",
        latency_ms=round(latency, 2),
        details={"candidates_in": len(candidates), "reranked_out": len(reranked)},
    )

    return {
        "reranked_chunks": reranked,
        "workflow_steps": state.get("workflow_steps", []) + [step],
        "rerank_ms": round(latency, 2),
    }

