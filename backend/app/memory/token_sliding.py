from dataclasses import dataclass, field

from app.configs import get_settings
from app.llm import generate_text, count_message_tokens
from app.memory.base import BaseMemoryManager
from app.memory.const import SUMMARY_PROMPT

settings = get_settings()

@dataclass
class TokenSlidingMemory(BaseMemoryManager):

    def build_messages(self) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        if self.summary:
            messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Conversation memory summary:\n\n"
                        f"{self.summary}"
                    ),
                }
            )

        recent_window = (
            self._build_token_window()
        )

        messages.extend(recent_window)

        return messages

    def should_summarize(self) -> bool:
        total_tokens = 0

        for message in self.recent_messages:
            total_tokens += (
                count_message_tokens(message)
            )

        return (
                total_tokens
                >= settings.summary_trigger_tokens
        )

    async def summarize(self) -> None:
        recent_window = (
            self._build_token_window()
        )

        recent_ids = {
            id(message)
            for message in recent_window
        }

        old_messages = [
            message
            for message in self.recent_messages
            if id(message) not in recent_ids
        ]

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

        if self.summary:
            summarize_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "Existing summary:\n\n"
                        f"{self.summary}"
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
            summarize_messages,
            temperature=0.2,
        )

        self.summary = new_summary.strip()

        self.recent_messages = recent_window

    def _build_token_window(
            self,
    ) -> list[dict]:
        selected_messages = []

        total_tokens = 0

        for message in reversed(
                self.recent_messages,
        ):
            message_tokens = (
                count_message_tokens(message)
            )

            if (
                    total_tokens + message_tokens
                    > settings.recent_window_tokens
            ):
                break

            selected_messages.append(message)

            total_tokens += message_tokens

        selected_messages.reverse()

        return selected_messages