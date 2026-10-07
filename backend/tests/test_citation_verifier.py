import pytest
from app.agents.nodes.citation_verifier import citation_verifier_node
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_citation_verifier_parses_and_links():
    state: AgentState = {
        "query": "What is Raft?",
        "conversation_id": None,
        "conversation_history": [],
        "top_k": 5,
        "use_reranker": True,
        "strategy_override": None,
        "classification": "factual",
        "needs_retrieval": True,
        "entities": [],
        "rewritten_queries": ["What is Raft?"],
        "retrieval_strategy": "single_hop_hybrid",
        "retrieved_chunks": [],
        "reranked_chunks": [
            {
                "chunk_id": "chunk-aaa",
                "document_id": "doc-111",
                "filename": "raft_paper.pdf",
                "page_number": 3,
                "content": "Raft is a consensus protocol using leader election and log replication.",
                "rerank_score": 0.94,
            },
            {
                "chunk_id": "chunk-bbb",
                "document_id": "doc-222",
                "filename": "paxos.pdf",
                "page_number": 1,
                "content": "Paxos is an alternative consensus protocol.",
                "rerank_score": 0.72,
            },
        ],
        "compressed_context": "",
        "raw_answer": "Raft uses leader election and log replication [1] to maintain safety.",
        "answer": "",
        "citations": [],
        "is_grounded": True,
        "grounding_score": 1.0,
        "grounding_explanation": None,
        "workflow_steps": [],
        "query_analysis_ms": 0.0,
        "retrieval_ms": 0.0,
        "rerank_ms": 0.0,
        "llm_generation_ms": 0.0,
        "verification_ms": 0.0,
        "total_latency_ms": 0.0,
        "error": None,
    }

    result = await citation_verifier_node(state)

    citations = result["citations"]
    assert len(citations) == 1
    assert citations[0].id == "1"
    assert citations[0].chunk_id == "chunk-aaa"
    assert citations[0].filename == "raft_paper.pdf"
    assert citations[0].page == 3
    assert citations[0].relevance_score == 0.94

