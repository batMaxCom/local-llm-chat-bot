from dataclasses import dataclass

from app.configs import get_settings
from app.database.semantic_memory import SemanticMemory
from app.llm import count_message_tokens
from app.memory.schemas import MemoryState
from app.const import (
    SYSTEM_PROMPT,
    TITLE_PROMPT,
)
from app.prompt.schemas import (
    PromptBuildResult,
)

settings = get_settings()


@dataclass
class PromptBuilder:

    max_context_tokens: int = (
        settings.max_context_tokens
    )

    reserved_output_tokens: int = (
        settings.reserved_output_tokens
    )

    system_prompt: str = SYSTEM_PROMPT

    def build_prompt(
        self,
        memory_state: MemoryState,
    ) -> PromptBuildResult:
        """
        effective_budget - максимальное количество токенов,
        которое можно потратить на input prompt
        Эти токены идут на: system prompt, summary, recent messages
        Остальные - на генерацию ответа модели
        """
        prompt_messages = []

        total_tokens = 0
        effective_budget = (
            self.max_context_tokens
            - self.reserved_output_tokens
        )

        system_message = {
            "role": "system",
            "content": self.system_prompt,
        }

        prompt_messages.append(
            system_message,
        )

        system_tokens = (
            count_message_tokens(
                system_message,
            )
        )

        total_tokens += system_tokens


        if memory_state.semantic:
            semantic_message = (
                self._build_semantic_section(
                    memory_state.semantic,
                )
            )

            semantic_tokens = (
                count_message_tokens(
                    semantic_message,
                )
            )

            if (
                total_tokens
                + semantic_tokens
                <= effective_budget
            ):
                prompt_messages.append(
                    semantic_message,
                )

                total_tokens += (
                    semantic_tokens
                )

        summary_tokens = 0

        if memory_state.summary:
            summary_message = {
                "role": "assistant",
                "content": (
                    "Conversation summary:\n\n"
                    f"{memory_state.summary}"
                ),
            }

            prompt_messages.append(
                summary_message,
            )

            summary_tokens = (
                count_message_tokens(
                    summary_message,
                )
            )

            total_tokens += summary_tokens

        recent_messages = (
            self._build_recent_window(
                messages=(
                    memory_state.recent_messages
                ),
                current_tokens=total_tokens,
                max_tokens=effective_budget,
            )
        )

        recent_tokens = sum(
            count_message_tokens(message)
            for message in recent_messages
        )

        total_tokens += recent_tokens

        prompt_messages.extend(
            recent_messages,
        )

        return PromptBuildResult(
            messages=prompt_messages,
            total_tokens=total_tokens,
            summary_tokens=summary_tokens,
            semantic_tokens=semantic_tokens,
            recent_tokens=recent_tokens,
        )

    @staticmethod
    def _build_semantic_section(
        semantic_memories: list[
            SemanticMemory
        ],
    ) -> dict:
        lines = []

        for memory in semantic_memories:
            lines.append(
                (
                    f"[{memory.category}] "
                    f"{memory.content}"
                )
            )

        content = (
            "Persistent semantic memory:\n\n"
            + "\n".join(lines)
        )

        return {
            "role": "assistant",
            "content": content,
        }

    def build_title_prompt(
        self,
        memory_state: MemoryState,
    ) -> list[dict]:
        relevant_messages = (
            memory_state.recent_messages[:6]
        )

        conversation_text = (
            self._messages_to_text(
                relevant_messages,
            )
        )

        if memory_state.summary:
            conversation_text = (
                "Conversation summary:\n\n"
                f"{memory_state.summary}\n\n"
                "Recent messages:\n\n"
                f"{conversation_text}"
            )

        return [
            {
                "role": "system",
                "content": TITLE_PROMPT,
            },
            {
                "role": "user",
                "content": conversation_text,
            },
        ]

    def _build_recent_window(
        self,
        messages: list[dict],
        current_tokens: int,
        max_tokens: int,
    ) -> list[dict]:
        selected_messages = []

        total_tokens = current_tokens

        for message in reversed(messages):
            message_tokens = (
                count_message_tokens(
                    message,
                )
            )

            if (
                total_tokens
                + message_tokens
                > max_tokens
            ):
                break

            selected_messages.append(
                message,
            )

            total_tokens += message_tokens

        selected_messages.reverse()

        return selected_messages

    @staticmethod
    def _messages_to_text(
        messages: list[dict],
    ) -> str:
        lines = []

        for message in messages:
            role = message["role"]

            content = message["content"]

            lines.append(
                f"{role.upper()}: {content}"
            )

        return "\n".join(lines)