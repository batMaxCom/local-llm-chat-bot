import uuid
from uuid import UUID

from fastapi import FastAPI, WebSocket, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.llm import generate_stream
from app.memory import SummaryMemoryManager
from app.services import ChatSessionService

app = FastAPI()

@app.router.get("/chats")
async def get_all_chats(
        session = Depends(get_session),
        service = Depends(ChatSessionService)
):
    return await service.all(session)

@app.router.post("/chats")
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


@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    chat_id: UUID,
    websocket: WebSocket,
    service=Depends(ChatSessionService),
    session: AsyncSession = Depends(get_session),
):
    chat = await service.one_only(session, chat_id)
    if chat is None:
        return
    await websocket.accept()
    memory = SummaryMemoryManager()
    memory.summary = chat.summary
    memory.recent_messages = chat.context
    try:
        while True:
            user_message = (
                await websocket.receive_text()
            )
            if (
                    not chat.title
                    and len(chat.context) >= 6
            ):
                title = memory.generate_title()

                await service.update_title(session, chat_id, title)
                await session.commit()
                await websocket.send(title)
            memory.add_user_message(user_message)

            messages = memory.build_messages()

            assistant_response = ""

            for chunk in generate_stream(messages):
                assistant_response += chunk

                await websocket.send_text(chunk)

            memory.add_assistant_message(
                assistant_response
            )
            if memory.should_summarize():
                memory.summarize()
                await service.update_summary(session, chat_id, memory.summary)

            await websocket.send_text("[END]")
            await service.update_context(session, chat_id, memory.recent_messages)
            await session.commit()

    except Exception as error:
        print(f"WebSocket error: {error}")

    finally:
        await websocket.close()