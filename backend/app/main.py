import uuid
from uuid import UUID

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.chats import CHAT_ROUTER
from app.routers.websocket import WS_ROUTER
from app.routers.message import MESSAGE_ROUTER

app = FastAPI()

app.include_router(WS_ROUTER)
app.include_router(CHAT_ROUTER)
app.include_router(MESSAGE_ROUTER)
