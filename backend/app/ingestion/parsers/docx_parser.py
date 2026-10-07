from pathlib import Path
from typing import Any, Dict, List
from app.core.errors import IngestionError
from app.core.logging import logger


class DocxParser:
    """Extracts structured text, headings, and paragraphs from DOCX documents."""

    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        sections = []
        try:
            import docx
            doc = docx.Document(file_path)
            current_section = "Introduction"
            current_text_blocks = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue

                if paragraph.style.name.startswith("Heading"):
                    if current_text_blocks:
                        sections.append({
                            "page_number": 1,
                            "section": current_section,
                            "text": "\n".join(current_text_blocks),
                        })
                        current_text_blocks = []
                    current_section = text
                else:
                    current_text_blocks.append(text)

            if current_text_blocks:
                sections.append({
                    "page_number": 1,
                    "section": current_section,
                    "text": "\n".join(current_text_blocks),
                })
        except ImportError:
            logger.warning("python-docx is not installed. Using raw text fallback for DOCX.")
            try:
                with open(file_path, "rb") as f:
                    raw = f.read().decode("latin-1", errors="ignore")
                sections.append({
                    "page_number": 1,
                    "section": "Raw Extraction",
                    "text": raw[:10000],
                })
            except Exception as e:
                raise IngestionError(f"Failed to read DOCX file: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise IngestionError(f"Failed to parse DOCX document: {e}") from e

        return sections

