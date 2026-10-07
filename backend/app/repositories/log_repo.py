from typing import List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evaluation import EvaluationRun
from app.models.retrieval_log import RetrievalLog


class LogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_retrieval(
        self,
        query: str,
        rewritten_query: Optional[str],
        strategy: str,
        top_k: int,
        retrieved_chunk_ids: List[str],
        reranked_chunk_ids: List[str],
        scores: dict,
        retrieval_latency_ms: float,
        rerank_latency_ms: float,
        llm_latency_ms: float,
        total_latency_ms: float,
    ) -> RetrievalLog:
        log_entry = RetrievalLog(
            query=query,
            rewritten_query=rewritten_query,
            strategy=strategy,
            top_k=top_k,
            retrieved_chunk_ids=retrieved_chunk_ids,
            reranked_chunk_ids=reranked_chunk_ids,
            scores=scores,
            retrieval_latency_ms=retrieval_latency_ms,
            rerank_latency_ms=rerank_latency_ms,
            llm_latency_ms=llm_latency_ms,
            total_latency_ms=total_latency_ms,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def list_recent_logs(self, limit: int = 50) -> List[RetrievalLog]:
        result = await self.db.execute(
            select(RetrievalLog).order_by(desc(RetrievalLog.created_at)).limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self) -> dict:
        total_queries = await self.db.scalar(select(func.count(RetrievalLog.id))) or 0
        avg_total_latency = (
            await self.db.scalar(select(func.avg(RetrievalLog.total_latency_ms))) or 0.0
        )
        avg_retrieval_latency = (
            await self.db.scalar(select(func.avg(RetrievalLog.retrieval_latency_ms))) or 0.0
        )
        avg_llm_latency = (
            await self.db.scalar(select(func.avg(RetrievalLog.llm_latency_ms))) or 0.0
        )

        # Strategy breakdown
        strategy_rows = await self.db.execute(
            select(RetrievalLog.strategy, func.count(RetrievalLog.id))
            .group_by(RetrievalLog.strategy)
            .order_by(desc(func.count(RetrievalLog.id)))
        )
        strategies = [{"strategy": row[0], "count": row[1]} for row in strategy_rows.all()]

        return {
            "total_queries": total_queries,
            "avg_latency_ms": round(float(avg_total_latency), 2),
            "avg_retrieval_latency_ms": round(float(avg_retrieval_latency), 2),
            "avg_llm_latency_ms": round(float(avg_llm_latency), 2),
            "strategies": strategies,
        }

    async def save_evaluation(
        self, run_name: str, dataset_size: int, metrics: dict, report_markdown: Optional[str] = None
    ) -> EvaluationRun:
        eval_run = EvaluationRun(
            run_name=run_name,
            dataset_size=dataset_size,
            metrics=metrics,
            report_markdown=report_markdown,
        )
        self.db.add(eval_run)
        await self.db.flush()
        return eval_run

    async def list_evaluations(self, limit: int = 10) -> List[EvaluationRun]:
        result = await self.db.execute(
            select(EvaluationRun).order_by(desc(EvaluationRun.created_at)).limit(limit)
        )
        return list(result.scalars().all())

