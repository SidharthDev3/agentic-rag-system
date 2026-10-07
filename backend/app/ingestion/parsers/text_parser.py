from pathlib import Path
from typing import Any, Dict, List
from app.core.errors import IngestionError


class TextParser:
    """Extracts text from plain text (.txt) files with encoding detection."""

    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        if content is None:
            raise IngestionError(f"Unable to decode text file {file_path}")

        # Split into logical sections by double line breaks if long
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        return [{
            "page_number": 1,
            "section": "General",
            "text": content.strip(),
        }]

