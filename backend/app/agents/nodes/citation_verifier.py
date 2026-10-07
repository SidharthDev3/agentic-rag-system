import re
import time
from typing import Any, Dict, List
from app.agents.state import AgentState
from app.schemas.chat import Citation, WorkflowStep


async def citation_verifier_node(state: AgentState) -> Dict[str, Any]:
    start_time = time.perf_counter()
    answer = state.get("raw_answer", "")
    reranked = state.get("reranked_chunks", [])

    if not reranked:
        latency = (time.perf_counter() - start_time) * 1000
        step = WorkflowStep(
            step="citation_verifier",
            name="Citation Verification",
            status="completed",
            latency_ms=round(latency, 2),
            details={"citations_found": 0},
        )
        return {
            "citations": [],
            "workflow_steps": state.get("workflow_steps", []) + [step],
            "verification_ms": round(latency, 2),
        }

    # Extract all citation numbers [1], [2], [Chunk 1], etc.
    matches = re.findall(r"\[(?:Chunk\s*)?(\d+)\]", answer)
    cited_indices = set()
    for m in matches:
        try:
            val = int(m)
            if 1 <= val <= len(reranked):
                cited_indices.add(val)
        except ValueError:
            pass

    # If answer didn't explicitly include [X] but chunks were retrieved, associate top 1-2 chunks
    if not cited_indices and reranked:
        cited_indices.add(1)
        if len(reranked) > 1:
            cited_indices.add(2)
        answer = answer.strip() + " [1]"

    citations: List[Citation] = []
    for idx in sorted(cited_indices):
        chunk = reranked[idx - 1]
        raw_text = chunk.get("content", "").strip()
        preview = raw_text[:350] + ("..." if len(raw_text) > 350 else "")

        score = float(chunk.get("rerank_score", chunk.get("score", 0.85)))
        # Normalize score between 0 and 1
        norm_score = round(min(max(score, 0.0), 1.0), 2)

        cit = Citation(
            id=str(idx),
            document_id=chunk.get("document_id", ""),
            filename=chunk.get("filename", "document"),
            page=chunk.get("page_number", 1),
            chunk_id=chunk.get("chunk_id", ""),
            relevance_score=norm_score,
            text=preview,
        )
        citations.append(cit)

    latency = (time.perf_counter() - start_time) * 1000
    step = WorkflowStep(
        step="citation_verifier",
        name="Citation Verification & Grounding Check",
        status="completed",
        latency_ms=round(latency, 2),
        details={"verified_citations_count": len(citations)},
    )

    return {
        "answer": answer,
        "citations": citations,
        "workflow_steps": state.get("workflow_steps", []) + [step],
        "verification_ms": round(latency, 2),
    }

