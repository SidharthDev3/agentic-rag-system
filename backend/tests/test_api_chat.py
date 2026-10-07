import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_endpoint(async_client: AsyncClient):
    payload = {
        "query": "Hello, how does NexusRAG work?",
        "top_k": 3,
    }

    resp = await async_client.post("/api/v1/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "answer" in data
    assert "conversation_id" in data
    assert "routing_strategy" in data
    assert "latency_breakdown" in data
    assert isinstance(data["citations"], list)
    assert isinstance(data["workflow_steps"], list)


@pytest.mark.asyncio
async def test_conversations_api(async_client: AsyncClient):
    # Create conversation
    create_resp = await async_client.post(
        "/api/v1/conversations", json={"title": "Test Thread"}
    )
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    # List conversations
    list_resp = await async_client.get("/api/v1/conversations")
    assert list_resp.status_code == 200
    assert any(c["id"] == conv_id for c in list_resp.json()["conversations"])

    # Get conversation
    get_resp = await async_client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv_id

    # Delete conversation
    del_resp = await async_client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_resp.status_code == 200

