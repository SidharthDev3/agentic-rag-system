from pathlib import Path
from typing import Any, Dict, List
from app.core.errors import IngestionError
from app.core.logging import logger


class PDFParser:
    """Extracts text, metadata, and per-page content from PDF documents using PyMuPDF."""

    @staticmethod
    def parse(file_path: Path) -> List[Dict[str, Any]]:
        pages_content = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                if text:
                    pages_content.append({
                        "page_number": page_num + 1,
                        "text": text,
                        "section": f"Page {page_num + 1}",
                    })
            doc.close()
        except ImportError:
            logger.warning("PyMuPDF (fitz) is not installed. Using raw text fallback for PDF.")
            try:
                with open(file_path, "rb") as f:
                    raw = f.read().decode("latin-1", errors="ignore")
                pages_content.append({
                    "page_number": 1,
                    "text": raw[:10000],
                    "section": "Raw Extraction",
                })
            except Exception as e:
                raise IngestionError(f"Failed to read PDF file: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise IngestionError(f"Failed to parse PDF document: {e}") from e

        return pages_content

