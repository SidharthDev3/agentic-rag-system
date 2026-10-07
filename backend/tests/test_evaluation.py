import pytest
from app.evaluation.metrics import (
    calculate_citation_correctness,
    calculate_faithfulness,
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
)
from app.schemas.chat import Citation


def test_evaluation_metrics():
    retrieved = ["doc_a.pdf", "doc_b.pdf", "doc_c.pdf"]

    # Recall
    assert calculate_recall_at_k(retrieved, "doc_b.pdf") == 1.0
    assert calculate_recall_at_k(retrieved, "doc_z.pdf") == 0.0

    # Precision@2
    assert calculate_precision_at_k(retrieved, "doc_a.pdf", k=2) == 0.5
    assert calculate_precision_at_k(retrieved, "doc_z.pdf", k=2) == 0.0

    # MRR
    assert calculate_mrr(retrieved, "doc_a.pdf") == 1.0
    assert calculate_mrr(retrieved, "doc_b.pdf") == 0.5
    assert calculate_mrr(retrieved, "doc_c.pdf") == 1.0 / 3.0

    # Faithfulness
    context = "NexusRAG uses hybrid retrieval combining vector and keyword search."
    good_answer = "The system uses hybrid retrieval with vector search."
    hallucinated_answer = "The system uses quantum entanglement processors on Mars."

    score_good = calculate_faithfulness(good_answer, context)
    score_bad = calculate_faithfulness(hallucinated_answer, context)
    assert score_good > score_bad

    # Citation correctness
    chunks = [{"chunk_id": "c1"}, {"chunk_id": "c2"}]
    cits = [
        Citation(
            id="1",
            document_id="d1",
            filename="doc.pdf",
            chunk_id="c1",
            relevance_score=0.9,
            text="sample text",
        )
    ]
    assert calculate_citation_correctness(cits, chunks) == 1.0

