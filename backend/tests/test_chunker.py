import pytest
from app.ingestion.chunker import SemanticChunker


def test_semantic_chunker_basic():
    chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
    sections = [
        {
            "page_number": 1,
            "section": "Introduction",
            "text": "This is a sentence. " * 10,
        }
    ]

    chunks = chunker.create_chunks(
        document_id="doc-123",
        filename="test.txt",
        parsed_sections=sections,
    )

    assert len(chunks) > 1
    assert chunks[0]["document_id"] == "doc-123"
    assert chunks[0]["source"] == "test.txt"
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["section"] == "Introduction"
    assert chunks[0]["token_count"] > 0
    assert "token_count" in chunks[0]["chunk_metadata"]


def test_semantic_chunker_preserves_short_text():
    chunker = SemanticChunker(chunk_size=500, chunk_overlap=50)
    sections = [
        {
            "page_number": 1,
            "section": "Quick Summary",
            "text": "A brief summary that easily fits within one chunk.",
        }
    ]

    chunks = chunker.create_chunks(
        document_id="doc-456",
        filename="quick.md",
        parsed_sections=sections,
    )

    assert len(chunks) == 1
    assert chunks[0]["content"] == "A brief summary that easily fits within one chunk."

