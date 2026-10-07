from typing import Any, Dict, List
from app.core.config import settings


class HybridFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining vector and keyword search results.
    RRF score: score(d) = sum( weight / (k + rank(d)) )
    """

    @staticmethod
    def fuse(
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        dense_weight: float = settings.RETRIEVAL_DENSE_WEIGHT,
        sparse_weight: float = settings.RETRIEVAL_SPARSE_WEIGHT,
        k: int = settings.RRF_K,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        # 1. Score dense results
        for rank, item in enumerate(dense_results):
            cid = item["chunk_id"]
            if cid not in chunks_map:
                chunks_map[cid] = dict(item)
            rrf_val = dense_weight / (k + (rank + 1))
            scores[cid] = scores.get(cid, 0.0) + rrf_val

        # 2. Score sparse results
        for rank, item in enumerate(sparse_results):
            cid = item["chunk_id"]
            if cid not in chunks_map:
                chunks_map[cid] = dict(item)
            rrf_val = sparse_weight / (k + (rank + 1))
            scores[cid] = scores.get(cid, 0.0) + rrf_val

        # 3. Create sorted list of combined results
        combined = []
        for cid, score in scores.items():
            chunk_data = dict(chunks_map[cid])
            chunk_data["score"] = score
            chunk_data["retrieval_type"] = "hybrid_rrf"
            combined.append(chunk_data)

        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:top_k]

