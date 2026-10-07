import hashlib
import math
from typing import List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._st_model = None
        self._openai_client = None

    def _get_st_model(self):
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model: {self.model_name}")
                self._st_model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(
                    f"SentenceTransformer model '{self.model_name}' could not be loaded ({e}). "
                    "Falling back to deterministic semantic hashing."
                )
                self.provider = "mock"
        return self._st_model

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY or "dummy",
                base_url=settings.LLM_BASE_URL,
            )
        return self._openai_client

    def _deterministic_hash_embed(self, text: str) -> List[float]:
        """
        Deterministic, dense semantic hashing embedding for offline test & fallback mode.
        Generates normalized vector of requested dimension with word n-gram hashes.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for i, word in enumerate(words):
            # Unigram hash
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 4) % 2 == 0 else -1.0
            vec[idx] += sign

            # Bigram hash for sequence awareness
            if i > 0:
                bigram = f"{words[i-1]}_{word}"
                bh = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                bidx = bh % self.dimension
                bsign = 1.0 if (bh >> 4) % 2 == 0 else -1.0
                vec[bidx] += 0.5 * bsign

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def get_embedding(self, text: str) -> List[float]:
        embeddings = await self.get_embeddings([text])
        return embeddings[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # 1. Deterministic Mock
        if self.provider == "mock" or not settings.LLM_API_KEY and self.provider == "openai":
            return [self._deterministic_hash_embed(t) for t in texts]

        # 2. Sentence Transformers
        if self.provider == "sentence_transformers":
            model = self._get_st_model()
            if model is not None:
                try:
                    vectors = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                    return vectors.tolist()
                except Exception as e:
                    logger.warning(f"SentenceTransformer encoding failed: {e}. Using deterministic fallback.")
                    return [self._deterministic_hash_embed(t) for t in texts]
            return [self._deterministic_hash_embed(t) for t in texts]

        # 3. OpenAI Embeddings
        if self.provider == "openai":
            try:
                client = self._get_openai_client()
                response = await client.embeddings.create(
                    model=self.model_name or "text-embedding-3-small",
                    input=texts,
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                logger.warning(f"OpenAI embedding call failed: {e}. Using deterministic fallback.")
                return [self._deterministic_hash_embed(t) for t in texts]

        return [self._deterministic_hash_embed(t) for t in texts]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a, b in zip(v1, v2)))
        norm2 = math.sqrt(sum(b * b for a, b in zip(v1, v2)))
        if norm1 <= 0 or norm2 <= 0:
            return 0.0
        return float(dot / (norm1 * norm2))


embedding_service = EmbeddingService()

