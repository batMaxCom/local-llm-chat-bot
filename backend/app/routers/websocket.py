from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_session
from app.llm import generate_stream, generate_text
from app.memory.schemas import MemoryState
from app.memory.token_sliding import TokenSlidingMemory
from app.prompt.builder import PromptBuilder
from app.semantic.extractor import SemanticExtractor
from app.semantic.service import SemanticMemoryService
from app.service.chat_session import ChatSessionService
from app.service.message import MessageService

WS_ROUTER = APIRouter(prefix="/ws")

@WS_ROUTER.websocket("/{chat_id}")
async def websocket_endpoint(
    chat_id: UUID,
    websocket: WebSocket,
    memory_service = Depends(ChatSessionService),
    message_service = Depends(MessageService),
    semantic_service = Depends(SemanticMemoryService),
    extractor = Depends(SemanticExtractor),
    session: AsyncSession = Depends(get_session),
):
    chat = await memory_service.load_only(session, chat_id)
    if chat is None:
        return
    await websocket.accept()
    semantic_memory_list = await semantic_service.get_recent_facts(session, chat.id)
    memory_state = MemoryState(
        summary=chat.summary,
        semantic=semantic_memory_list,
        recent_messages=chat.context
    )
    memory = TokenSlidingMemory(
        memory_state=memory_state,
    )
    builder = PromptBuilder()
    try:
        while True:
            user_message = (
                await websocket.receive_text()
            )
            if (
                    not chat.title
                    and len(chat.context) >= 6
            ):
                title_prompt = builder.build_title_prompt(memory_state=memory.memory_state)

                title = await generate_text(
                   messages=title_prompt,
                   temperature=0.1,
                )
                title = (
                    title.strip()
                    .replace('"', "")
                    .replace("\n", " ")
                )
                await memory_service.update_title(session, chat_id, title)

                await session.commit()
                await websocket.send(title)
            await memory.add_user_message(user_message)

            prompt = builder.build_prompt(
                memory_state=memory.memory_state,
            )
            print(
                {
                    "event": "prompt_generated",
                    "total_tokens": prompt.total_tokens,
                    "summary_tokens": prompt.summary_tokens,
                    "semantic_tokens": prompt.semantic_tokens,
                    "recent_tokens": prompt.recent_tokens
                }
            )

            assistant_response = ""

            async for chunk in generate_stream(prompt):
                assistant_response += chunk

                await websocket.send_text(chunk)

            await memory.add_assistant_message(
                assistant_response
            )
            if await memory.should_summarize():
                (old_messages, recent_messages) = memory.split_runtime_messages()
                await memory.summarize(old_messages, recent_messages)
                await memory_service.update_summary(session, chat_id, memory.memory_state.summary)

                facts = await extractor.extract(old_messages)
                await semantic_service.save_facts(
                    session=session,
                    session_id=chat_id,
                    facts=facts,
                )

            await websocket.send_text("[END]")
            await memory_service.update_context(session, chat_id, memory.memory_state.recent_messages)

            await message_service.add(session, chat_id, "user", user_message)
            await message_service.add(session, chat_id, "assistant", assistant_response)

            await session.commit()

    except Exception as error:
        print(f"WebSocket error: {error}")
        raise error from None

    finally:
        await websocket.close()
