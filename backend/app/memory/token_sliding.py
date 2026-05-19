from app.configs import get_settings
from app.llm import (
    count_message_tokens,
    generate_text,
)
from app.prompt.const import SUMMARY_PROMPT
from app.memory.interface import MemoryManager

settings = get_settings()


class TokenSlidingMemory(
    MemoryManager,
):

    async def add_user_message(
        self,
        content: str,
    ) -> None:
        self.memory_state.recent_messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    async def add_assistant_message(
        self,
        content: str,
    ) -> None:
        self.memory_state.recent_messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

    async def should_summarize(
        self,
    ) -> bool:
        """Проверяем не превышает ли количество токенов в message со значением summary_trigger"""
        total_tokens = sum(
            count_message_tokens(message)
            for message in (
                self.memory_state.recent_messages
            )
        )

        return (
            total_tokens
            >= settings.summary_trigger_tokens
        )

    async def summarize(
        self,
    ) -> None:
        (
            old_messages,
            recent_messages,
        ) = self._split_runtime_messages()

        if not old_messages:
            return

        conversation_text = (
            self._messages_to_text(
                old_messages,
            )
        )

        summarize_messages = [
            {
                "role": "system",
                "content": SUMMARY_PROMPT,
            }
        ]

        if self.memory_state.summary:
            summarize_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Existing summary:\n\n"
                        f"{self.memory_state.summary}"
                    ),
                }
            )

        summarize_messages.append(
            {
                "role": "user",
                "content": conversation_text,
            }
        )

        new_summary = await generate_text(
            messages=summarize_messages,
            temperature=0.2,
        )

        self.memory_state.summary = (
            new_summary.strip()
        )

        self.memory_state.recent_messages = (
            recent_messages
        )

    def _split_runtime_messages(
        self,
    ) -> tuple[list[dict], list[dict]]:
        recent_messages = []

        total_tokens = 0

        for message in reversed(
            self.memory_state.recent_messages,
        ):
            message_tokens = (
                count_message_tokens(
                    message,
                )
            )

            if (
                total_tokens
                + message_tokens
                > settings.runtime_window_tokens
            ):
                break

            recent_messages.append(
                message,
            )

            total_tokens += message_tokens

        recent_messages.reverse()

        recent_count = len(
            recent_messages,
        )

        old_messages = (
            self.memory_state.recent_messages[
                :-recent_count
            ]
        )

        return (
            old_messages,
            recent_messages,
        )

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