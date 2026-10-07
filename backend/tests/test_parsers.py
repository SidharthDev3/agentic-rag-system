import tempfile
from pathlib import Path
import pytest
from app.ingestion.parsers.markdown_parser import MarkdownParser
from app.ingestion.parsers.text_parser import TextParser


def test_markdown_parser_hierarchical_sections():
    md_content = """# System Overview
This is the main overview of the platform.

## Sub-System A
Details regarding Sub-System A components.

## Sub-System B
Details regarding Sub-System B architecture.
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_content)
        temp_path = Path(f.name)

    try:
        sections = MarkdownParser.parse(temp_path)
        assert len(sections) >= 3
        section_titles = [s["section"] for s in sections]
        assert "System Overview" in section_titles
        assert "Sub-System A" in section_titles
        assert "Sub-System B" in section_titles
    finally:
        temp_path.unlink(missing_ok=True)


def test_text_parser():
    txt_content = "This is a simple plain text document.\n\nIt contains two distinct paragraphs."
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(txt_content)
        temp_path = Path(f.name)

    try:
        sections = TextParser.parse(temp_path)
        assert len(sections) == 1
        assert "plain text document" in sections[0]["text"]
        assert sections[0]["page_number"] == 1
    finally:
        temp_path.unlink(missing_ok=True)

