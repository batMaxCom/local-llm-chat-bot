from dataclasses import dataclass, field


SYSTEM_PROMPT = """
You are a helpful AI assistant.
Answer clearly and concisely.
"""


@dataclass
class ChatSession:
    messages: list[dict] = field(
        default_factory=lambda: [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]
    )

    def add_user_message(self, content: str) -> None:
        self.messages.append(
            {
                "role": "user",
                "content": content,
            }
        )

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )