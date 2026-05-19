from app.configs import get_settings
from app.memory.base import BaseMemoryManager

settings = get_settings()

class SlidingWindow(BaseMemoryManager):
    """
    Храним только последние N сообщений.
    Плюсы:
        - просто
        - быстро
        - идеально для MVP
    Минусы:
        - бот забывает старые темы
    """

    def build_messages(self) -> list[dict]:
        self.recent_messages = self.recent_messages[
            -settings.max_recent_messages:
        ]

        return [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            *self.recent_messages,
        ]