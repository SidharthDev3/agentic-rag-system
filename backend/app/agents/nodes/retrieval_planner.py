import time
from typing import Any, Dict
from app.agents.state import AgentState
from app.schemas.chat import WorkflowStep


async def retrieval_planner_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    classification = state.get("classification", "factual")
    requested_top_k = state.get("top_k", 5)

    if classification == "comparison":
        strategy = "multi_hop_comparison"
        fetch_k = max(requested_top_k * 2, 10)
    elif classification in {"multi_doc", "analytical"}:
        strategy = "multi_hop_analytical"
        fetch_k = max(requested_top_k * 2, 12)
    elif classification == "summarization":
        strategy = "broad_context_summary"
        fetch_k = max(requested_top_k * 2, 12)
    else:
        strategy = "single_hop_hybrid"
        fetch_k = max(requested_top_k * 2, 8)

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="retrieval_planner",
        name="Retrieval Strategy Planner",
        status="completed",
        latency_ms=round(latency, 2),
        details={"strategy": strategy, "candidate_fetch_k": fetch_k},
    )

    return {
        "retrieval_strategy": strategy,
        "workflow_steps": state.get("workflow_steps", []) + [step],
    }

