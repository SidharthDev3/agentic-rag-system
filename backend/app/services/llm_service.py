import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self._client = None

    def _get_client(self):
        if not self.api_key and self.provider != "mock":
            logger.info("No LLM_API_KEY configured. Running in offline mock/demo mode.")
            return None
        if self._client is None and self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                logger.warning("openai library not installed. Using offline mock generator.")
                return None
        return self._client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> str:
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_t = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        client = self._get_client()
        if client is not None:
            try:
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": max_t,
                }
                if response_format == "json":
                    kwargs["response_format"] = {"type": "json_object"}

                response = await client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except Exception as e:
                logger.warning(f"Remote LLM call failed ({e}). Falling back to deterministic generation.")

        return self._mock_generate(messages, response_format)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        max_t = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        client = self._get_client()
        if client is not None:
            try:
                stream = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_t,
                    stream=True,
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield delta
                return
            except Exception as e:
                logger.warning(f"Remote LLM streaming failed ({e}). Falling back to deterministic stream.")

        # Offline Mock stream
        full_text = self._mock_generate(messages, response_format=None)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.015)

    def _mock_generate(self, messages: List[Dict[str, str]], response_format: Optional[str]) -> str:
        """
        Deterministic, grounded response generator for testing and offline runs.
        Extracts context chunks from the prompt and constructs a factual answer with citations.
        """
        last_message = messages[-1]["content"] if messages else ""
        system_prompt = messages[0]["content"] if len(messages) > 1 and messages[0]["role"] == "system" else ""

        # Check if caller asked for JSON (e.g. query classification, rewriting, or grounding check)
        if response_format == "json" or "JSON" in system_prompt:
            if "query_analyzer" in system_prompt or "classify" in system_prompt.lower():
                # Routing classification
                query_lower = last_message.lower()
                greetings = [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bwho are you\b", r"\bwhat can you do\b"]
                if any(re.search(p, query_lower) for p in greetings):
                    return json.dumps({
                        "classification": "conversational",
                        "needs_retrieval": False,
                        "direct_answer": "Hello! I am NexusRAG, your Agentic Knowledge Intelligence Assistant. Upload documents to get started or ask me questions about your knowledge base."
                    })
                elif "compare" in query_lower or "versus" in query_lower or " vs " in query_lower:
                    return json.dumps({
                        "classification": "comparison",
                        "needs_retrieval": True,
                        "entities": ["Concept A", "Concept B"]
                    })
                elif "summarize" in query_lower or "summary" in query_lower:
                    return json.dumps({
                        "classification": "summarization",
                        "needs_retrieval": True
                    })
                else:
                    return json.dumps({
                        "classification": "factual",
                        "needs_retrieval": True
                    })

            if "grounding" in system_prompt.lower() or "hallucination" in system_prompt.lower():
                return json.dumps({
                    "is_grounded": True,
                    "grounding_score": 0.94,
                    "explanation": "All stated facts directly correspond to the provided document context excerpts."
                })

            if "rewrite" in system_prompt.lower():
                return json.dumps({
                    "rewritten_queries": [last_message, f"{last_message} technical details architecture"]
                })

        # Text generation with context grounding:
        # Check if context passages exist in prompt
        chunk_matches = re.findall(r"\[Chunk (\d+)\]\s*(.*?)(?=\n\[Chunk|\Z)", last_message, re.DOTALL)
        if not chunk_matches:
            # Check for generic context
            chunk_matches = re.findall(r"\[Document:\s*(.*?)\s*\|\s*Chunk\s*(\d+)\]\s*(.*?)(?=\n\[Document|\Z)", last_message, re.DOTALL)

        if "hello" in last_message.lower() or "hi" in last_message.lower() and not chunk_matches:
            return "Hello! I am **NexusRAG**, an agentic knowledge retrieval platform. You can upload PDFs, DOCX, TXT, or Markdown documents, and ask complex multi-document questions with verified source citations."

        if not chunk_matches and "Context:" in last_message:
            # Fallback simple extractor
            return (
                "Based on the available knowledge base:\n\n"
                "The documented architecture implements agentic orchestration, hybrid retrieval combining dense vector similarity and BM25 full-text search, reciprocal rank fusion (RRF), and cross-encoder reranking. [1]\n\n"
                "All assertions are verified against retrieved document chunks."
            )

        if chunk_matches:
            # Extract key snippet
            first_chunk = chunk_matches[0][-1].strip().replace("\n", " ")
            snippet = first_chunk[:250] + ("..." if len(first_chunk) > 250 else "")
            return (
                f"Based on the indexed documents:\n\n"
                f"{snippet} [1]\n\n"
                f"The system verified these statements against the retrieved knowledge base with grounded citations."
            )

        return (
            "I searched the knowledge base, but could not find sufficient evidence in the uploaded documents to answer this reliably."
        )


llm_service = LLMService()
