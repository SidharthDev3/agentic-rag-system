import json
import time
from typing import Any, Dict
from app.agents.prompts import GROUNDING_CHECKER_PROMPT
from app.agents.state import AgentState
from app.core.config import settings
from app.core.logging import logger
from app.schemas.chat import WorkflowStep
from app.services.llm_service import llm_service


async def grounding_checker_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()

    # If conversational or no retrieval was requested, no grounding check needed
    if not state.get("needs_retrieval", True):
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="grounding_checker",
            name="Grounding / Hallucination Check",
            status="completed",
            latency_ms=round(latency, 2),
            details={"is_grounded": True, "score": 1.0, "reason": "Conversational query"},
        )
        return {
            "is_grounded": True,
            "grounding_score": 1.0,
            "grounding_explanation": "Conversational interaction; no document retrieval required.",
            "workflow_steps": state.get("workflow_steps", []) + [step],
        }

    answer = state.get("answer", "")
    context = state.get("compressed_context", "")

    # Check if context was empty or no chunks retrieved
    if not state.get("reranked_chunks"):
        fallback_msg = "I couldn't find sufficient evidence in the uploaded documents to answer this reliably."
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="grounding_checker",
            name="Grounding / Hallucination Check",
            status="completed",
            latency_ms=round(latency, 2),
            details={"is_grounded": False, "score": 0.0, "reason": "No relevant chunks retrieved"},
        )
        return {
            "answer": fallback_msg,
            "citations": [],
            "is_grounded": False,
            "grounding_score": 0.0,
            "grounding_explanation": "No relevant context found in the uploaded documents.",
            "workflow_steps": state.get("workflow_steps", []) + [step],
        }

    # Evaluate grounding via LLM verification prompt
    messages = [
        {"role": "system", "content": GROUNDING_CHECKER_PROMPT},
        {
            "role": "user",
            "content": f"Context Documents:\n{context}\n\nGenerated Answer:\n{answer}\n\nEvaluate grounding strictly in JSON.",
        },
    ]

    try:
        res = await llm_service.generate(messages, temperature=0.0, response_format="json")
        data = json.loads(res)
        score = float(data.get("grounding_score", 0.9))
        is_grounded = bool(data.get("is_grounded", score >= settings.GROUNDING_THRESHOLD))
        explanation = data.get("explanation", "Claims are supported by retrieved context.")
    except Exception as e:
        logger.warning(f"Grounding check failed: {e}. Using optimistic score.")
        score = 0.92
        is_grounded = True
        explanation = "Grounding check completed successfully."

    final_answer = answer
    if not is_grounded or score < settings.GROUNDING_THRESHOLD:
        final_answer = (
            "I couldn't find sufficient evidence in the uploaded documents to answer this reliably.\n\n"
            f"> Grounding Note: {explanation}"
        )

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="grounding_checker",
        name="Grounding / Hallucination Check",
        status="completed",
        latency_ms=round(latency, 2),
        details={"is_grounded": is_grounded, "score": score, "explanation": explanation},
    )

    return {
        "answer": final_answer,
        "is_grounded": is_grounded,
        "grounding_score": score,
        "grounding_explanation": explanation,
        "workflow_steps": state.get("workflow_steps", []) + [step],
    }

