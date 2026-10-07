import json
import time
from typing import Any, Dict
from app.agents.prompts import QUERY_REWRITER_PROMPT
from app.agents.state import AgentState
from app.core.logging import logger
from app.schemas.chat import WorkflowStep
from app.services.llm_service import llm_service


async def query_rewriter_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    query = state["query"]
    classification = state.get("classification", "factual")

    messages = [
        {"role": "system", "content": QUERY_REWRITER_PROMPT},
        {"role": "user", "content": f"Query: {query}\nClassification: {classification}"},
    ]

    try:
        response_text = await llm_service.generate(messages, temperature=0.0, response_format="json")
        data = json.loads(response_text)
        rewritten = data.get("rewritten_queries", [query])
        if not rewritten or not isinstance(rewritten, list):
            rewritten = [query]
    except Exception as e:
        logger.warning(f"Query rewriter failed: {e}. Keeping original query.")
        rewritten = [query]

    # Ensure original query is always in search consideration
    if query not in rewritten:
        rewritten.insert(0, query)

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="query_rewriter",
        name="Query Rewriter & Planner",
        status="completed",
        latency_ms=round(latency, 2),
        details={"rewritten_queries": rewritten, "count": len(rewritten)},
    )

    return {
        "rewritten_queries": rewritten,
        "workflow_steps": state.get("workflow_steps", []) + [step],
    }

