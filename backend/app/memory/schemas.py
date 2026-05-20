from dataclasses import dataclass

from app.database.semantic_memory import SemanticMemory


@dataclass
class MemoryState:
    summary: str | None
    semantic : list[SemanticMemory] | None
    recent_messages: list[dict]
