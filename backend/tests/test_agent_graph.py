import pytest
from app.agents.graph import run_agentic_rag


@pytest.mark.asyncio
async def test_agent_graph_conversational_routing():
    # Conversational greeting should bypass retrieval
    state = await run_agentic_rag(query="Hello there!")

    assert state["classification"] == "conversational"
    assert not state["needs_retrieval"]
    assert len(state["citations"]) == 0
    assert "NexusRAG" in state["answer"]
    assert state["total_latency_ms"] >= 0


@pytest.mark.asyncio
async def test_agent_graph_factual_execution():
    state = await run_agentic_rag(query="What is hybrid retrieval?", top_k=3)

    assert state["needs_retrieval"]
    assert state["workflow_steps"]
    step_names = [s.step for s in state["workflow_steps"]]
    assert "query_analyzer" in step_names
    assert "generator" in step_names
    assert "citation_verifier" in step_names
    assert "grounding_checker" in step_names

