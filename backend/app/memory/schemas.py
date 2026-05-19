from dataclasses import dataclass


@dataclass
class MemoryState:
    summary: str | None
    recent_messages: list[dict]