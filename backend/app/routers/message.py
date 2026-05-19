from uuid import UUID

from fastapi import APIRouter, Depends

from app.database.base import get_session
from app.service.message import MessageService

MESSAGE_ROUTER = APIRouter(prefix="/message")

@MESSAGE_ROUTER.get("")
async def get_paginated_message(
        session_id: str,
        before_id: int | None = None,
        limit: int = 10,
        session=Depends(get_session),
        service=Depends(MessageService),
):
    session_id = UUID(session_id)
    return await service.load_paginated(session, session_id, before_id, limit)
