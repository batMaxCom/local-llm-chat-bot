from dataclasses import dataclass

from app.configs import get_settings
from app.llm import generate_text
from app.memory.base import BaseMemoryManager
from app.memory.const import SUMMARY_PROMPT

settings = get_settings()

@dataclass
class SummaryMemoryManager(BaseMemoryManager):

    def should_summarize(self) -> bool:
        return (
            len(self.recent_messages)
            >= settings.summary_trigger_messages
        )

    def build_summary_message(self) -> dict | None:
        if not self.summary:
            return None

        return {
            "role": "assistant",
            "content": (
                "Conversation memory summary:\n\n"
                f"{self.summary}"
            ),
        }

    def build_messages(self) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            }
        ]

        summary_message = self.build_summary_message()

        if summary_message:
            messages.append(summary_message)

        messages.extend(self.recent_messages)

        return messages

    async def summarize(self) -> None:
        old_messages = self.recent_messages[
            :-settings.max_recent_messages
        ]

        if not old_messages:
            return

        conversation_text = self._messages_to_text(
            old_messages,
        )

        summary_input = []

        if self.summary:
            summary_input.append(
                {
                    "role": "assistant",
                    "content": (
                        "Existing memory summary:\n\n"
                        f"{self.summary}"
                    ),
                }
            )

        summary_input.extend(
            [
                {
                    "role": "system",
                    "content": SUMMARY_PROMPT,
                },
                {
                    "role": "user",
                    "content": conversation_text,
                },
            ]
        )

        new_summary = await generate_text(
            messages=summary_input,
            temperature=0.2,
        )

        self.summary = new_summary.strip()

        self.recent_messages = self.recent_messages[
            -settings.max_recent_messages:
        ]