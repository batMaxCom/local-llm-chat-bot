from dataclasses import dataclass, field

from app.chat import SYSTEM_PROMPT
from app.llm import generate_text

SUMMARY_PROMPT = """
You are a conversation memory manager.

Your task:
Create a concise structured memory summary.

Keep:
- user goals
- important technical decisions
- preferences
- architecture decisions
- current tasks
- important facts

Remove:
- repetition
- casual conversation
- unimportant details

Return concise structured summary.

Format:

User:
- ...

Project:
- ...

Architecture:
- ...

Current Tasks:
- ...

Important Context:
- ...
"""

TITLE_PROMPT = """
You are a chat title generator.

Generate a very short title for the conversation.

Rules:
- max 8 words
- concise
- informative
- no quotes
- no punctuation at the end
- focus on main technical topic

Examples:
- FastAPI WebSocket Chat Memory
- RabbitMQ Consumer Refactoring
- Qwen Context Window Problem
- Alembic Restore Error
"""

MAX_RECENT_MESSAGES = 10
SUMMARY_TRIGGER_MESSAGES = 15


@dataclass
class SummaryMemoryManager:
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

    def should_summarize(self) -> bool:
        return (
            len(self.recent_messages)
            >= SUMMARY_TRIGGER_MESSAGES
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

    def summarize(self) -> None:
        old_messages = self.recent_messages[
            :-MAX_RECENT_MESSAGES
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

        new_summary = generate_text(
            messages=summary_input,
            temperature=0.2,
        )

        self.summary = new_summary.strip()

        self.recent_messages = self.recent_messages[
            -MAX_RECENT_MESSAGES:
        ]

    def generate_title(self) -> str:
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

        title = generate_text(
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
    