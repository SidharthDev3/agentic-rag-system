import time
from typing import Any, Dict
from app.agents.state import AgentState
from app.schemas.chat import WorkflowStep


async def context_compressor_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    chunks = state.get("reranked_chunks", [])

    if not chunks:
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="context_compressor",
            name="Context Compression & Structuring",
            status="completed",
            latency_ms=round(latency, 2),
            details={"chunks_compressed": 0, "total_characters": 0},
        )
        return {
            "compressed_context": "No relevant documents found.",
            "workflow_steps": state.get("workflow_steps", []) + [step],
        }

    formatted_passages = []
    total_chars = 0

    for idx, c in enumerate(chunks, start=1):
        filename = c.get("filename", "unknown")
        page = c.get("page_number", 1)
        section = c.get("section", "General")
        content = c.get("content", "").strip()

        header = f"[Chunk {idx}] (Source: {filename} | Page {page} | Section: {section})"
        passage = f"{header}\n{content}"
        formatted_passages.append(passage)
        total_chars += len(passage)

    compressed_context = "\n\n---\n\n".join(formatted_passages)

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="context_compressor",
        name="Context Compression & Structuring",
        status="completed",
        latency_ms=round(latency, 2),
        details={"chunks_compressed": len(chunks), "total_characters": total_chars},
    )

    return {
        "compressed_context": compressed_context,
        "workflow_steps": state.get("workflow_steps", []) + [step],
    }

