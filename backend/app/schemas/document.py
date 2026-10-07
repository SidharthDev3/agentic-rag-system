from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.chunk import ChunkResponse


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int = 0
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(DocumentBase):
    id: str
    content_hash: str
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    chunks: List[ChunkResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]

