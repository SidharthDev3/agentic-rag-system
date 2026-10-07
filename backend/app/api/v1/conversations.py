from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_conversation_repo
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """List recent conversation sessions."""
    conversations, total = await conv_repo.list_conversations(skip=skip, limit=limit)
    response_items = []
    for c in conversations:
        response_items.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=len(c.messages) if c.messages else 0,
            )
        )
    return ConversationListResponse(total=total, conversations=response_items)


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Create a new chat conversation thread."""
    conv = await conv_repo.create(title=payload.title or "New Conversation")
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Retrieve conversation details with all historical messages and source citations."""
    conv = await conv_repo.get_by_id(conversation_id, load_messages=True)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found",
        )

    messages = [MessageResponse.model_validate(m) for m in conv.messages]
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(messages),
        messages=messages,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: str,
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Delete a conversation thread and its message history."""
    deleted = await conv_repo.delete(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found",
        )
    return {"message": "Conversation deleted successfully", "id": conversation_id}

