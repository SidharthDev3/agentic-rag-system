import re
from pathlib import Path
from typing import Any, Dict, List
from app.core.errors import IngestionError


class MarkdownParser:
    """Parses Markdown (.md) documents preserving heading structure and sections."""

    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            raise IngestionError(f"Error reading Markdown file: {e}") from e

        # Match headers (# Header)
        lines = content.split("\n")
        sections = []
        current_section = "Overview"
        current_lines = []

        header_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

        for line in lines:
            match = header_pattern.match(line.strip())
            if match:
                if current_lines:
                    text_block = "\n".join(current_lines).strip()
                    if text_block:
                        sections.append({
                            "page_number": 1,
                            "section": current_section,
                            "text": text_block,
                        })
                    current_lines = []
                current_section = match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            text_block = "\n".join(current_lines).strip()
            if text_block:
                sections.append({
                    "page_number": 1,
                    "section": current_section,
                    "text": text_block,
                })

        return sections if sections else [{
            "page_number": 1,
            "section": "Overview",
            "text": content.strip()
        }]

