import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_lifecycle(async_client: AsyncClient):
    # 1. Health check
    health_resp = await async_client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    # 2. Upload text document
    file_content = b"# Document Title\nThis is test text for indexing into NexusRAG."
    files = {"file": ("test_doc.md", io.BytesIO(file_content), "text/markdown")}

    upload_resp = await async_client.post("/api/v1/documents/upload", files=files)
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["filename"] == "test_doc.md"
    assert doc_data["status"] == "indexed"
    assert doc_data["chunk_count"] >= 1

    # 3. List documents
    list_resp = await async_client.get("/api/v1/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # 4. Get document detail with chunks
    detail_resp = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["chunks"]) >= 1

    # 5. Delete document
    del_resp = await async_client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 200

    # 6. Verify deleted
    get_del = await async_client.get(f"/api/v1/documents/{doc_id}")
    assert get_del.status_code == 404

