import json
import time
from typing import Any, Dict
from app.agents.prompts import QUERY_ANALYZER_PROMPT
from app.agents.state import AgentState
from app.core.logging import logger
from app.schemas.chat import WorkflowStep
from app.services.llm_service import llm_service


async def query_analyzer_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    query = state["query"]

    # Quick heuristic check for greetings
    query_clean = query.strip().lower()
    if query_clean in {"hi", "hello", "hey", "who are you", "what can you do?", "help"}:
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="query_analyzer",
            name="Query Understanding",
            status="completed",
            latency_ms=round(latency, 2),
            details={"classification": "conversational", "needs_retrieval": False},
        )
        return {
            "classification": "conversational",
            "needs_retrieval": False,
            "entities": [],
            "raw_answer": "Hello! I am NexusRAG, your Agentic Knowledge Intelligence Assistant. Upload documents or ask me questions about your ingested knowledge base.",
            "workflow_steps": state.get("workflow_steps", []) + [step],
            "query_analysis_ms": round(latency, 2),
        }

    # Manual strategy override if provided
    if state.get("strategy_override"):
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="query_analyzer",
            name="Query Understanding",
            status="completed",
            latency_ms=round(latency, 2),
            details={"classification": state["strategy_override"], "needs_retrieval": True},
        )
        return {
            "classification": state["strategy_override"],
            "needs_retrieval": True,
            "entities": [],
            "workflow_steps": state.get("workflow_steps", []) + [step],
            "query_analysis_ms": round(latency, 2),
        }

    # LLM classification
    messages = [
        {"role": "system", "content": QUERY_ANALYZER_PROMPT},
        {"role": "user", "content": f"Analyze this query: {query}"},
    ]

    try:
        response_text = await llm_service.generate(messages, temperature=0.0, response_format="json")
        data = json.loads(response_text)
        classification = data.get("classification", "factual")
        needs_retrieval = data.get("needs_retrieval", True)
        entities = data.get("entities", [])
        direct_answer = data.get("direct_answer")
    except Exception as e:
        logger.warning(f"Query analyzer JSON parse failed: {e}. Defaulting to factual lookup.")
        classification = "factual"
        needs_retrieval = True
        entities = []
        direct_answer = None

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="query_analyzer",
        name="Query Understanding",
        status="completed",
        latency_ms=round(latency, 2),
        details={"classification": classification, "needs_retrieval": needs_retrieval, "entities": entities},
    )

    updates: Dict[str, Any] = {
        "classification": classification,
        "needs_retrieval": needs_retrieval,
        "entities": entities,
        "workflow_steps": state.get("workflow_steps", []) + [step],
        "query_analysis_ms": round(latency, 2),
    }
    if not needs_retrieval and direct_answer:
        updates["raw_answer"] = direct_answer

    return updates

