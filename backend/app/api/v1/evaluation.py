from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_log_repo
from app.evaluation.benchmark import benchmark_runner
from app.repositories.log_repo import LogRepository
from app.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    MetricScore,
)

router = APIRouter(prefix="/evaluation", tags=["Evaluation & Benchmarks"])


@router.get("/latest", response_model=EvaluationRunResponse)
async def get_latest_evaluation(log_repo: LogRepository = Depends(get_log_repo)):
    """Retrieve the most recent RAG evaluation benchmark run."""
    evals = await log_repo.list_evaluations(limit=1)
    if not evals:
        # If no prior evaluation, run one or return empty benchmark
        result = await benchmark_runner.run_benchmark(top_k=5)
        eval_run = await log_repo.save_evaluation(
            run_name="Initial Benchmark",
            dataset_size=result["dataset_size"],
            metrics=result["metrics"],
            report_markdown=result["report_markdown"],
        )
        evals = [eval_run]

    latest = evals[0]
    metrics_list = [
        MetricScore(
            name=k.replace("_", " ").title(),
            score=v,
            description=f"Evaluation metric {k}",
        )
        for k, v in latest.metrics.items()
        if isinstance(v, (int, float))
    ]

    return EvaluationRunResponse(
        id=latest.id,
        run_name=latest.run_name,
        dataset_size=latest.dataset_size,
        metrics=latest.metrics,
        detailed_metrics=metrics_list,
        report_markdown=latest.report_markdown,
        created_at=latest.created_at,
    )


@router.post("/run", response_model=EvaluationRunResponse)
async def run_evaluation(
    payload: EvaluationRunRequest,
    log_repo: LogRepository = Depends(get_log_repo),
):
    """Trigger an execution of the evaluation benchmark suite."""
    result = await benchmark_runner.run_benchmark(top_k=payload.top_k)
    saved = await log_repo.save_evaluation(
        run_name=payload.run_name or "Ad-hoc Benchmark",
        dataset_size=result["dataset_size"],
        metrics=result["metrics"],
        report_markdown=result["report_markdown"],
    )

    metrics_list = [
        MetricScore(
            name=k.replace("_", " ").title(),
            score=v,
            description=f"Evaluation metric {k}",
        )
        for k, v in saved.metrics.items()
        if isinstance(v, (int, float))
    ]

    return EvaluationRunResponse(
        id=saved.id,
        run_name=saved.run_name,
        dataset_size=saved.dataset_size,
        metrics=saved.metrics,
        detailed_metrics=metrics_list,
        report_markdown=saved.report_markdown,
        created_at=saved.created_at,
    )

