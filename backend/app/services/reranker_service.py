import re
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from app.core.logging import logger


class RerankerService:
    def __init__(self):
        self.reranker_type = settings.RERANKER_TYPE.lower()
        self.model_name = settings.RERANKER_MODEL
        self._cross_encoder = None

    def _get_cross_encoder(self):
        if self._cross_encoder is None and self.reranker_type == "cross_encoder":
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder reranker: {self.model_name}")
                self._cross_encoder = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(
                    f"CrossEncoder '{self.model_name}' could not be initialized ({e}). "
                    "Using heuristic lexical-semantic reranker fallback."
                )
                self.reranker_type = "heuristic"
        return self._cross_encoder

    def _heuristic_score(self, query: str, text: str) -> float:
        """
        Calculates exact word overlap, partial stem matches, and position weighting.
        Returns a normalized score between 0.0 and 1.0.
        """
        q_tokens = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
        if not q_tokens:
            return 0.5
        t_tokens = re.findall(r"\w+", text.lower())
        if not t_tokens:
            return 0.0

        matches = sum(1 for token in q_tokens if token in t_tokens)
        ratio = matches / len(q_tokens)

        # Boost if query words appear in close proximity
        text_lower = text.lower()
        phrase_boost = 0.2 if query.lower() in text_lower else 0.0

        # Title/early match boost
        early_tokens = t_tokens[:30]
        early_matches = sum(1 for token in q_tokens if token in early_tokens)
        early_boost = 0.1 * (early_matches / len(q_tokens))

        raw_score = (0.7 * ratio) + phrase_boost + early_boost
        return min(max(raw_score, 0.0), 1.0)

    async def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidates (each candidate must have a 'content' field).
        Attaches 'rerank_score' to each candidate and returns sorted top_k.
        """
        if not candidates:
            return []

        encoder = self._get_cross_encoder()
        if encoder is not None:
            try:
                pairs = [[query, c.get("content", "")] for c in candidates]
                scores = encoder.predict(pairs)
                for c, score in zip(candidates, scores):
                    # Sigmoid or min-max normalization if necessary
                    c["rerank_score"] = float(score)
            except Exception as e:
                logger.warning(f"CrossEncoder prediction failed: {e}. Falling back to heuristic.")
                for c in candidates:
                    c["rerank_score"] = self._heuristic_score(query, c.get("content", ""))
        else:
            for c in candidates:
                c["rerank_score"] = self._heuristic_score(query, c.get("content", ""))

        # Sort descending by rerank_score
        sorted_candidates = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return sorted_candidates[:top_k]


reranker_service = RerankerService()

