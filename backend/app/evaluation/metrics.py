import re
from typing import Any, Dict, List


def calculate_recall_at_k(retrieved_sources: List[str], expected_source: str) -> float:
    """Computes Recall@K: 1.0 if expected document is in retrieved list, else 0.0."""
    if not expected_source:
        return 1.0
    return 1.0 if any(expected_source.lower() in s.lower() for s in retrieved_sources) else 0.0


def calculate_precision_at_k(retrieved_sources: List[str], expected_source: str, k: int = 5) -> float:
    """Computes Precision@K: proportion of top-k retrieved sources that match expected source."""
    if not expected_source or not retrieved_sources:
        return 0.0
    top_k_sources = retrieved_sources[:k]
    matches = sum(1 for s in top_k_sources if expected_source.lower() in s.lower())
    return matches / len(top_k_sources)


def calculate_mrr(retrieved_sources: List[str], expected_source: str) -> float:
    """Computes Mean Reciprocal Rank (MRR): 1 / rank of first relevant retrieved item."""
    if not expected_source:
        return 1.0
    for rank, source in enumerate(retrieved_sources, start=1):
        if expected_source.lower() in source.lower():
            return 1.0 / rank
    return 0.0


def calculate_context_relevance(chunks: List[Dict[str, Any]], expected_keywords: List[str]) -> float:
    """Evaluates whether retrieved chunks contain the key semantic concepts needed."""
    if not expected_keywords:
        return 1.0
    if not chunks:
        return 0.0

    combined_text = " ".join(c.get("content", "").lower() for c in chunks)
    found = sum(1 for kw in expected_keywords if kw.lower() in combined_text)
    return found / len(expected_keywords)


def calculate_citation_correctness(citations: List[Any], chunks: List[Dict[str, Any]]) -> float:
    """Checks whether generated citations accurately reference existing retrieved chunks."""
    if not citations:
        return 1.0 if not chunks else 0.0
    chunk_ids = {c.get("chunk_id") for c in chunks}
    valid_citations = sum(1 for cit in citations if getattr(cit, "chunk_id", "") in chunk_ids)
    return valid_citations / len(citations)


def calculate_faithfulness(answer: str, context: str) -> float:
    """Computes textual support ratio between answer claims and context."""
    if not answer or not context:
        return 0.0
    answer_sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer) if len(s.strip()) > 15]
    if not answer_sentences:
        return 1.0

    supported = 0
    context_lower = context.lower()
    for sentence in answer_sentences:
        words = [w for w in re.findall(r"\w+", sentence.lower()) if len(w) > 3]
        if not words:
            supported += 1
            continue
        # Check if majority of salient words exist in context
        overlap = sum(1 for w in words if w in context_lower)
        if (overlap / len(words)) >= 0.5:
            supported += 1

    return round(supported / len(answer_sentences), 2)

