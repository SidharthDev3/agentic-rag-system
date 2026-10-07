from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricScore(BaseModel):
    name: str
    score: float
    description: str


class EvaluationTestCase(BaseModel):
    query: str
    expected_relevant_doc: Optional[str] = None
    expected_keywords: List[str] = Field(default_factory=list)
    category: str = "factual"


class EvaluationRunRequest(BaseModel):
    run_name: Optional[str] = "Benchmark Run"
    top_k: int = 5


class EvaluationRunResponse(BaseModel):
    id: str
    run_name: str
    dataset_size: int
    metrics: Dict[str, float]
    detailed_metrics: List[MetricScore] = Field(default_factory=list)
    report_markdown: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

