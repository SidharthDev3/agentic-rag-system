import time
from typing import Any, Dict
from app.agents.prompts import ANSWER_GENERATOR_PROMPT
from app.agents.state import AgentState
from app.schemas.chat import WorkflowStep
from app.services.llm_service import llm_service


async def answer_generator_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    query = state["query"]
    context = state.get("compressed_context", "")

    # Build prompt
    system_msg = ANSWER_GENERATOR_PROMPT
    user_msg = (
        f"User Question: {query}\n\n"
        f"Reference Context Documents:\n{context}\n\n"
        f"Provide a comprehensive, accurate answer grounded in the above context with citations."
    )

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    answer = await llm_service.generate(messages, temperature=0.1)

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="generator",
        name="Grounded Answer Synthesis",
        status="completed",
        latency_ms=round(latency, 2),
        details={"answer_length": len(answer)},
    )

    return {
        "raw_answer": answer,
        "answer": answer,
        "workflow_steps": state.get("workflow_steps", []) + [step],
        "llm_generation_ms": round(latency, 2),
    }

