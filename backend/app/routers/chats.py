import uuid
from uuid import UUID

from fastapi import APIRouter, Depends

from app.database.base import get_session
from app.service.chat_session import ChatSessionService

CHAT_ROUTER = APIRouter(prefix="/chats")

@CHAT_ROUTER.get("")
async def get_all_chats(
        session = Depends(get_session),
        service = Depends(ChatSessionService)
):
    return await service.load_many(session)

@CHAT_ROUTER.post("")
async def new_chats(
        session = Depends(get_session),
        service = Depends(ChatSessionService)
) -> UUID:
    chat_id = uuid.uuid4()
    await service.add(
        session,
        id=chat_id
    )
    return chat_id
