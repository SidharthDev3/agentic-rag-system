from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    token_count: int = 0
    page_number: Optional[int] = None
    section: Optional[str] = None
    source: str
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None
    similarity_score: Optional[float] = None
    rerank_score: Optional[float] = None
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkListResponse(BaseModel):
    total: int
    chunks: list[ChunkResponse]

