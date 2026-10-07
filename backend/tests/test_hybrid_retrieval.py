import pytest
from app.retrieval.hybrid_fusion import HybridFusion
from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_embedding_service_deterministic():
    service = EmbeddingService()
    emb1 = await service.get_embedding("distributed consensus protocol")
    emb2 = await service.get_embedding("distributed consensus protocol")
    emb3 = await service.get_embedding("unrelated organic cooking recipes")

    assert len(emb1) == service.dimension
    assert emb1 == emb2  # Deterministic

    sim_same = service.cosine_similarity(emb1, emb2)
    sim_diff = service.cosine_similarity(emb1, emb3)

    assert sim_same > 0.99
    assert sim_same > sim_diff


def test_reciprocal_rank_fusion():
    dense = [
        {"chunk_id": "c1", "content": "Text 1", "score": 0.9},
        {"chunk_id": "c2", "content": "Text 2", "score": 0.8},
        {"chunk_id": "c3", "content": "Text 3", "score": 0.7},
    ]
    sparse = [
        {"chunk_id": "c2", "content": "Text 2", "score": 4.5},
        {"chunk_id": "c4", "content": "Text 4", "score": 3.2},
        {"chunk_id": "c1", "content": "Text 1", "score": 2.1},
    ]

    fused = HybridFusion.fuse(dense_results=dense, sparse_results=sparse, k=60, top_k=3)

    assert len(fused) == 3
    # c2 was rank 2 in dense and rank 1 in sparse -> should score highest
    assert fused[0]["chunk_id"] == "c2"
    assert fused[0]["retrieval_type"] == "hybrid_rrf"

