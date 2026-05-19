from dataclasses import dataclass, field

from app.llm import generate_text
from app.memory.const import SYSTEM_PROMPT, TITLE_PROMPT


@dataclass
class BaseMemoryManager:
    system_prompt: str = SYSTEM_PROMPT
    title: str | None = None
    summary: str = ""

    recent_messages: list[dict] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.recent_messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def add_assistant_message(self, content: str) -> None:
        self.recent_messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

    async def generate_title(self) -> str:
        relevant_messages = self.recent_messages[:6]

        conversation_text = self._messages_to_text(
            relevant_messages,
        )

        messages = [
            {
                "role": "system",
                "content": TITLE_PROMPT,
            },
            {
                "role": "user",
                "content": conversation_text,
            },
        ]

        title = await generate_text(
            messages=messages,
            temperature=0.1,
        )

        self.title = (
            title.strip()
            .replace('"', "")
            .replace("\n", " ")
        )

        return self.title

    @staticmethod
    def _messages_to_text(
        messages: list[dict],
    ) -> str:
        lines = []

        for message in messages:
            role = message["role"].upper()
            content = message["content"]

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)
