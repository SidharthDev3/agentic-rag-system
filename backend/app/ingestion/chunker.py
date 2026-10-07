import re
from typing import Any, Dict, List
from app.core.config import settings


class SemanticChunker:
    """
    Intelligent hierarchical chunker that preserves document structure,
    section headers, page numbers, and offsets while respecting token/character limits.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text_recursively(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        separators = ["\n\n", "\n", ". ", "; ", ", ", " "]
        for sep in separators:
            parts = text.split(sep)
            if len(parts) > 1:
                chunks = []
                current_chunk = []
                current_len = 0

                for part in parts:
                    part_len = len(part) + len(sep)
                    if current_len + part_len > self.chunk_size and current_chunk:
                        chunk_str = sep.join(current_chunk).strip()
                        if chunk_str:
                            chunks.append(chunk_str)

                        # Overlap: keep trailing parts up to chunk_overlap
                        overlap_parts = []
                        overlap_len = 0
                        for p in reversed(current_chunk):
                            if overlap_len + len(p) <= self.chunk_overlap:
                                overlap_parts.insert(0, p)
                                overlap_len += len(p)
                            else:
                                break
                        current_chunk = list(overlap_parts)
                        current_len = sum(len(p) + len(sep) for p in current_chunk)

                    current_chunk.append(part)
                    current_len += part_len

                if current_chunk:
                    chunk_str = sep.join(current_chunk).strip()
                    if chunk_str:
                        chunks.append(chunk_str)

                if chunks:
                    return chunks

        # Fallback hard slice
        return [
            text[i : i + self.chunk_size].strip()
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap)
            if text[i : i + self.chunk_size].strip()
        ]

    def create_chunks(
        self,
        document_id: str,
        filename: str,
        parsed_sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        chunks_data = []
        global_chunk_idx = 0
        running_char_offset = 0

        for section_obj in parsed_sections:
            text = section_obj.get("text", "").strip()
            page_num = section_obj.get("page_number", 1)
            section_name = section_obj.get("section", "General")

            if not text:
                continue

            sub_chunks = self._split_text_recursively(text)

            for sub_chunk in sub_chunks:
                char_start = running_char_offset
                char_end = char_start + len(sub_chunk)
                running_char_offset = char_end + 1

                # Approximate token count (1 token ≈ 4 characters)
                token_count = max(1, len(sub_chunk.split()))

                chunk_entry = {
                    "document_id": document_id,
                    "chunk_index": global_chunk_idx,
                    "content": sub_chunk,
                    "token_count": token_count,
                    "page_number": page_num,
                    "section": section_name,
                    "source": filename,
                    "char_offset_start": char_start,
                    "char_offset_end": char_end,
                    "chunk_metadata": {
                        "filename": filename,
                        "section": section_name,
                        "page": page_num,
                        "token_count": token_count,
                    },
                }
                chunks_data.append(chunk_entry)
                global_chunk_idx += 1

        return chunks_data


semantic_chunker = SemanticChunker()

