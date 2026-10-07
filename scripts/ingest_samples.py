import asyncio
from pathlib import Path
import sys

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db.init_db import init_db
from app.db.session import async_session_factory
from app.services.ingestion_service import IngestionService


async def ingest_samples():
    print("=" * 60)
    print(" NEXUSRAG — SAMPLE DATASET INGESTION PIPELINE")
    print("=" * 60)
    print("1. Initializing database schema...")
    await init_db()

    sample_dir = Path(__file__).resolve().parent.parent / "sample_data"
    sample_files = list(sample_dir.glob("*.*"))

    if not sample_files:
        print(f"No sample files found in {sample_dir}")
        return

    print(f"2. Found {len(sample_files)} sample files to ingest:")
    for f in sample_files:
        print(f"   - {f.name} ({f.stat().st_size} bytes)")

    print("\n3. Ingesting documents...")
    async with async_session_factory() as session:
        service = IngestionService(session)
        for f in sample_files:
            try:
                print(f"   -> Ingesting {f.name}...", end=" ", flush=True)
                doc = await service.ingest_file(
                    file_path=f,
                    original_filename=f.name,
                    file_size=f.stat().st_size,
                )
                print(f"OK (ID: {doc.id[:8]}... | Chunks: {doc.chunk_count})")
            except Exception as e:
                print(f"FAILED ({e})")

    print("\n" + "=" * 60)
    print(" Sample ingestion completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(ingest_samples())

