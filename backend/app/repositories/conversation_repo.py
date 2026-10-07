from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, conversation_id: str, load_messages: bool = True) -> Optional[Conversation]:
        query = select(Conversation).where(Conversation.id == conversation_id)
        if load_messages:
            query = query.options(selectinload(Conversation.messages))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(self, skip: int = 0, limit: int = 50) -> tuple[List[Conversation], int]:
        count_res = await self.db.execute(select(func.count(Conversation.id)))
        total = count_res.scalar() or 0

        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create(self, title: str = "New Conversation") -> Conversation:
        conv = Conversation(title=title)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def update_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        conv = await self.get_by_id(conversation_id, load_messages=False)
        if conv:
            conv.title = title
            await self.db.flush()
        return conv

    async def delete(self, conversation_id: str) -> bool:
        conv = await self.get_by_id(conversation_id, load_messages=False)
        if conv:
            await self.db.delete(conv)
            await self.db.flush()
            return True
        return False

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[List[dict]] = None,
        routing_strategy: Optional[str] = None,
        latency_ms: Optional[float] = None,
        msg_metadata: Optional[dict] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations or [],
            routing_strategy=routing_strategy,
            latency_ms=latency_ms,
            msg_metadata=msg_metadata or {},
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

