import pytest
from app.services.reranker_service import RerankerService


@pytest.mark.asyncio
async def test_reranker_scoring():
    service = RerankerService()
    query = "two-phase commit coordinator protocol"
    candidates = [
        {"chunk_id": "c1", "content": "Bananas and apples are popular fresh fruits."},
        {
            "chunk_id": "c2",
            "content": "In two-phase commit, the coordinator protocol sends prepare messages.",
        },
        {"chunk_id": "c3", "content": "Database indexing speeds up SQL query lookups."},
    ]

    reranked = await service.rerank(query=query, candidates=candidates, top_k=2)

    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
    assert "rerank_score" in reranked[0]
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]

