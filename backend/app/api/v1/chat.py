import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.agents.graph import nexusrag_graph, run_agentic_rag
from app.api.deps import get_conversation_repo, get_log_repo
from app.core.logging import logger
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.log_repo import LogRepository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Citation,
    LatencyBreakdown,
    WorkflowStep,
)

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    log_repo: LogRepository = Depends(get_log_repo),
):
    """
    Standard synchronous chat endpoint invoking the full LangGraph Agentic RAG workflow.
    Returns generated answer with citations, grounding confidence, and telemetry.
    """
    # 1. Resolve or create conversation
    conv_id = request.conversation_id
    history_messages: List[Dict[str, str]] = []
    if conv_id:
        conv = await conv_repo.get_by_id(conv_id, load_messages=True)
        if conv and conv.messages:
            history_messages = [
                {"role": m.role, "content": m.content} for m in conv.messages[-6:]
            ]
    else:
        new_conv = await conv_repo.create(title=request.query[:50])
        conv_id = new_conv.id

    # 2. Add user message
    await conv_repo.add_message(
        conversation_id=conv_id,
        role="user",
        content=request.query,
    )

    # 3. Execute Agentic RAG Workflow
    state = await run_agentic_rag(
        query=request.query,
        conversation_id=conv_id,
        conversation_history=history_messages,
        top_k=request.top_k or 5,
        use_reranker=request.use_reranker if request.use_reranker is not None else True,
        strategy_override=request.strategy_override,
    )

    answer = state.get("answer", "")
    citations = state.get("citations", [])
    routing_strategy = state.get("classification", "factual")
    grounding_score = state.get("grounding_score", 1.0)
    is_grounded = state.get("is_grounded", True)
    grounding_explanation = state.get("grounding_explanation")

    latency_breakdown = LatencyBreakdown(
        query_analysis_ms=state.get("query_analysis_ms", 0.0),
        retrieval_ms=state.get("retrieval_ms", 0.0),
        rerank_ms=state.get("rerank_ms", 0.0),
        llm_generation_ms=state.get("llm_generation_ms", 0.0),
        verification_ms=state.get("verification_ms", 0.0),
        total_ms=state.get("total_latency_ms", 0.0),
    )

    # 4. Save assistant message
    asst_msg = await conv_repo.add_message(
        conversation_id=conv_id,
        role="assistant",
        content=answer,
        citations=[c.model_dump() for c in citations],
        routing_strategy=routing_strategy,
        latency_ms=state.get("total_latency_ms", 0.0),
        msg_metadata={
            "grounding_score": grounding_score,
            "is_grounded": is_grounded,
            "workflow_steps": [s.model_dump() for s in state.get("workflow_steps", [])],
        },
    )

    # 5. Log telemetry
    retrieved_chunk_ids = [c.get("chunk_id", "") for c in state.get("retrieved_chunks", [])]
    reranked_chunk_ids = [c.get("chunk_id", "") for c in state.get("reranked_chunks", [])]
    scores = {c.get("chunk_id", ""): float(c.get("score", 0.0)) for c in state.get("reranked_chunks", [])}

    await log_repo.log_retrieval(
        query=request.query,
        rewritten_query=(state.get("rewritten_queries") or [None])[0],
        strategy=routing_strategy,
        top_k=request.top_k or 5,
        retrieved_chunk_ids=retrieved_chunk_ids,
        reranked_chunk_ids=reranked_chunk_ids,
        scores=scores,
        retrieval_latency_ms=state.get("retrieval_ms", 0.0),
        rerank_latency_ms=state.get("rerank_ms", 0.0),
        llm_latency_ms=state.get("llm_generation_ms", 0.0),
        total_latency_ms=state.get("total_latency_ms", 0.0),
    )

    return ChatResponse(
        answer=answer,
        citations=citations,
        conversation_id=conv_id,
        message_id=asst_msg.id,
        routing_strategy=routing_strategy,
        grounding_score=grounding_score,
        is_grounded=is_grounded,
        grounding_explanation=grounding_explanation,
        latency_breakdown=latency_breakdown,
        workflow_steps=state.get("workflow_steps", []),
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    log_repo: LogRepository = Depends(get_log_repo),
):
    """
    Streaming Server-Sent Events (SSE) chat endpoint.
    Emits real-time workflow status updates, progressive answer tokens, citations, and completion telemetry.
    """
    conv_id = request.conversation_id
    if not conv_id:
        new_conv = await conv_repo.create(title=request.query[:50])
        conv_id = new_conv.id

    await conv_repo.add_message(
        conversation_id=conv_id,
        role="user",
        content=request.query,
    )

    async def event_generator() -> AsyncIterator[str]:
        # 1. Status: Analyzing
        yield f"data: {json.dumps({'type': 'status', 'step': 'query_analyzer', 'message': 'Understanding intent & classification...'})}\n\n"
        await asyncio.sleep(0.05)

        # 2. Run agent workflow
        state = await run_agentic_rag(
            query=request.query,
            conversation_id=conv_id,
            top_k=request.top_k or 5,
            use_reranker=request.use_reranker if request.use_reranker is not None else True,
            strategy_override=request.strategy_override,
        )

        # Emit intermediate step events for UI progress stepper
        for step in state.get("workflow_steps", []):
            yield f"data: {json.dumps({'type': 'step_completed', 'step': step.step, 'name': step.name, 'latency_ms': step.latency_ms})}\n\n"

        answer = state.get("answer", "")
        citations = [c.model_dump() for c in state.get("citations", [])]

        # 3. Stream tokens progressively
        yield f"data: {json.dumps({'type': 'status', 'step': 'generating', 'message': 'Streaming grounded response...'})}\n\n"
        words = answer.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
            await asyncio.sleep(0.015)

        # 4. Emit citations
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

        # 5. Save assistant message
        asst_msg = await conv_repo.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=answer,
            citations=citations,
            routing_strategy=state.get("classification", "factual"),
            latency_ms=state.get("total_latency_ms", 0.0),
            msg_metadata={
                "grounding_score": state.get("grounding_score", 1.0),
                "is_grounded": state.get("is_grounded", True),
            },
        )

        # 6. Log telemetry
        await log_repo.log_retrieval(
            query=request.query,
            rewritten_query=(state.get("rewritten_queries") or [None])[0],
            strategy=state.get("classification", "factual"),
            top_k=request.top_k or 5,
            retrieved_chunk_ids=[c.get("chunk_id", "") for c in state.get("retrieved_chunks", [])],
            reranked_chunk_ids=[c.get("chunk_id", "") for c in state.get("reranked_chunks", [])],
            scores={},
            retrieval_latency_ms=state.get("retrieval_ms", 0.0),
            rerank_latency_ms=state.get("rerank_ms", 0.0),
            llm_latency_ms=state.get("llm_generation_ms", 0.0),
            total_latency_ms=state.get("total_latency_ms", 0.0),
        )

        # 7. Final completion event
        done_payload = {
            "type": "done",
            "conversation_id": conv_id,
            "message_id": asst_msg.id,
            "grounding_score": state.get("grounding_score", 1.0),
            "is_grounded": state.get("is_grounded", True),
            "total_latency_ms": state.get("total_latency_ms", 0.0),
            "strategy": state.get("classification", "factual"),
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

