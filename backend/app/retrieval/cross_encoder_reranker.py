from typing import Any, Dict, List
from app.core.config import settings
from app.services.reranker_service import reranker_service


class CrossEncoderReranker:
    """Wraps RerankerService to prune and rerank hybrid search candidate chunks."""

    def __init__(self, top_k: int = settings.RERANK_TOP_K):
        self.top_k = top_k

    async def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        k = top_k or self.top_k
        if not candidates:
            return []

        reranked = await reranker_service.rerank(query=query, candidates=candidates, top_k=k)
        for item in reranked:
            item["retrieval_type"] = "reranked"
        return reranked

