from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_session
from app.llm import generate_stream
from app.memory.sliding_window import SlidingWindow
from app.memory.summary import SummaryMemoryManager
from app.memory.token_sliding import TokenSlidingMemory
from app.service.chat_session import ChatSessionService
from app.service.message import MessageService

WS_ROUTER = APIRouter(prefix="/ws")

@WS_ROUTER.websocket("/{chat_id}")
async def websocket_endpoint(
    chat_id: UUID,
    websocket: WebSocket,
    memory_service = Depends(ChatSessionService),
    message_service = Depends(MessageService),
    session: AsyncSession = Depends(get_session),
):
    chat = await memory_service.load_only(session, chat_id)
    if chat is None:
        return
    await websocket.accept()
    # memory = SummaryMemoryManager()
    # memory = SlidingWindow()
    memory = TokenSlidingMemory()
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

                await memory_service.update_title(session, chat_id, title)
                await session.commit()
                await websocket.send(title)
            memory.add_user_message(user_message)

            messages = memory.build_messages()

            assistant_response = ""

            async for chunk in generate_stream(messages):
                assistant_response += chunk

                await websocket.send_text(chunk)

            memory.add_assistant_message(
                assistant_response
            )
            # Summary
            if hasattr(memory, "should_summarize") and memory.should_summarize():
                await memory.summarize()
                await memory_service.update_summary(session, chat_id, memory.summary)

            await websocket.send_text("[END]")
            await memory_service.update_context(session, chat_id, memory.recent_messages)

            await message_service.add(session, chat_id, "user", user_message)
            await message_service.add(session, chat_id, "assistant", assistant_response)

            await session.commit()

    except Exception as error:
        print(f"WebSocket error: {error}")
        raise error from None

    finally:
        await websocket.close()
