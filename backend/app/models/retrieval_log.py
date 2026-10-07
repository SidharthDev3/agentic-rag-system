import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strategy: Mapped[str] = mapped_column(String(100), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    retrieved_chunk_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    reranked_chunk_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    scores: Mapped[Dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    retrieval_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rerank_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    llm_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

