import asyncio
import sys
from app.db.init_db import init_db
from app.evaluation.benchmark import benchmark_runner


async def main():
    print("=" * 70)
    print(" NEXUSRAG — AGENTIC EVALUATION BENCHMARK SUITE")
    print("=" * 70)
    print("Initializing test environment & database...")
    await init_db()

    print("\nRunning benchmark across evaluation test cases...")
    result = await benchmark_runner.run_benchmark(top_k=5)

    print("\n" + result["report_markdown"])
    print("=" * 70)
    print("Evaluation completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

