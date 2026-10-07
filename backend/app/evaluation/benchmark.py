import json
from pathlib import Path
from typing import Any, Dict, List
from app.agents.graph import run_agentic_rag
from app.core.logging import logger
from app.evaluation.metrics import (
    calculate_citation_correctness,
    calculate_context_relevance,
    calculate_faithfulness,
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
)


class BenchmarkRunner:
    def __init__(self, dataset_path: Path = None):
        if dataset_path is None:
            dataset_path = Path(__file__).parent / "dataset.json"
        self.dataset_path = dataset_path

    def load_dataset(self) -> List[Dict[str, Any]]:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def run_benchmark(self, top_k: int = 5) -> Dict[str, Any]:
        test_cases = self.load_dataset()
        results = []

        total_recall = 0.0
        total_precision = 0.0
        total_mrr = 0.0
        total_faithfulness = 0.0
        total_citation_corr = 0.0
        total_context_rel = 0.0
        total_retrieval_ms = 0.0
        total_e2e_ms = 0.0

        evaluated_count = 0

        for tc in test_cases:
            query = tc["query"]
            expected_doc = tc.get("expected_relevant_doc")
            expected_keywords = tc.get("expected_keywords", [])
            is_unanswerable = tc.get("expect_unanswerable", False)

            # Execute Agentic RAG
            state = await run_agentic_rag(query=query, top_k=top_k)

            retrieved = state.get("reranked_chunks", [])
            sources = [c.get("filename", "") for c in retrieved]
            answer = state.get("answer", "")
            context = state.get("compressed_context", "")
            citations = state.get("citations", [])

            # Compute metrics
            recall = calculate_recall_at_k(sources, expected_doc) if expected_doc else 1.0
            precision = calculate_precision_at_k(sources, expected_doc, k=top_k) if expected_doc else 1.0
            mrr = calculate_mrr(sources, expected_doc) if expected_doc else 1.0
            ctx_rel = calculate_context_relevance(retrieved, expected_keywords) if expected_keywords else 1.0
            cit_corr = calculate_citation_correctness(citations, retrieved)

            # Faithfulness
            if is_unanswerable:
                # If unanswerable, faithfulness is 1.0 if system refused to answer
                is_refused = "could not find sufficient evidence" in answer.lower()
                faith = 1.0 if is_refused else 0.5
            else:
                faith = calculate_faithfulness(answer, context)

            retrieval_ms = state.get("retrieval_ms", 0.0)
            total_ms = state.get("total_latency_ms", 0.0)

            total_recall += recall
            total_precision += precision
            total_mrr += mrr
            total_faithfulness += faith
            total_citation_corr += cit_corr
            total_context_rel += ctx_rel
            total_retrieval_ms += retrieval_ms
            total_e2e_ms += total_ms

            evaluated_count += 1
            results.append({
                "id": tc["id"],
                "query": query,
                "category": tc["category"],
                "recall_at_k": round(recall, 3),
                "precision_at_k": round(precision, 3),
                "mrr": round(mrr, 3),
                "faithfulness": round(faith, 3),
                "citation_correctness": round(cit_corr, 3),
                "context_relevance": round(ctx_rel, 3),
                "retrieval_latency_ms": round(retrieval_ms, 2),
                "total_latency_ms": round(total_ms, 2),
                "answer_preview": answer[:120] + "...",
            })

        count = max(1, evaluated_count)
        avg_metrics = {
            "retrieval_recall": round(total_recall / count, 3),
            "precision_at_k": round(total_precision / count, 3),
            "mrr": round(total_mrr, 3),
            "faithfulness": round(total_faithfulness / count, 3),
            "citation_correctness": round(total_citation_corr / count, 3),
            "context_relevance": round(total_context_rel / count, 3),
            "avg_retrieval_latency_ms": round(total_retrieval_ms / count, 2),
            "avg_e2e_latency_ms": round(total_e2e_ms / count, 2),
        }

        # Format markdown report
        markdown_report = self._format_report(avg_metrics, results)

        return {
            "dataset_size": count,
            "metrics": avg_metrics,
            "results": results,
            "report_markdown": markdown_report,
        }

    def _format_report(self, avg: Dict[str, float], results: List[Dict[str, Any]]) -> str:
        report = []
        report.append("# NexusRAG Evaluation Benchmark Report\n")
        report.append(f"**Test Cases Evaluated:** {len(results)}\n")
        report.append("## Overall Metrics Summary\n")
        report.append("| Metric | Score | Description |")
        report.append("| :--- | :--- | :--- |")
        report.append(f"| **Retrieval Recall** | `{avg['retrieval_recall']:.3f}` | Proportion of ground-truth docs retrieved |")
        report.append(f"| **Precision@K** | `{avg['precision_at_k']:.3f}` | Proportion of retrieved chunks that are relevant |")
        report.append(f"| **MRR** | `{avg['mrr']:.3f}` | Mean Reciprocal Rank of first relevant doc |")
        report.append(f"| **Faithfulness** | `{avg['faithfulness']:.3f}` | Ratio of claims supported by retrieved context |")
        report.append(f"| **Citation Correctness** | `{avg['citation_correctness']:.3f}` | Accuracy of chunk citation links |")
        report.append(f"| **Context Relevance** | `{avg['context_relevance']:.3f}` | Salient keyword coverage in context |")
        report.append(f"| **Avg Retrieval Latency** | `{avg['avg_retrieval_latency_ms']:.1f}ms` | Hybrid search + fusion execution time |")
        report.append(f"| **Avg End-to-End Latency** | `{avg['avg_e2e_latency_ms']:.1f}ms` | Full agentic pipeline response time |\n")

        report.append("## Per-Query Test Results\n")
        report.append("| Query | Category | Recall | Precision | Faithfulness | E2E Latency |")
        report.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in results:
            short_q = (r['query'][:38] + "...") if len(r['query']) > 40 else r['query']
            report.append(f"| {short_q} | `{r['category']}` | `{r['recall_at_k']}` | `{r['precision_at_k']}` | `{r['faithfulness']}` | `{r['total_latency_ms']}ms` |")

        return "\n".join(report)


benchmark_runner = BenchmarkRunner()

