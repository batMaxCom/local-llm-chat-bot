from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from app.memory.schemas import MemoryState


@dataclass
class MemoryManager(ABC):

    memory_state: MemoryState

    @abstractmethod
    async def add_user_message(
        self,
        content: str,
    ) -> None:
        pass

    @abstractmethod
    async def add_assistant_message(
        self,
        content: str,
    ) -> None:
        pass

    @abstractmethod
    async def should_summarize(
        self,
    ) -> bool:
        pass

    @abstractmethod
    async def summarize(
        self,
        old_messages: list[dict],
        recent_messages: list[dict]
    ) -> None:
        pass