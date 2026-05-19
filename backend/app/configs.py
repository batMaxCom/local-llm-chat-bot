from dataclasses import dataclass
from functools import lru_cache
from os import environ
from typing import Self


@dataclass(slots=True)
class AppConfig:
    max_recent_messages: int
    summary_trigger_messages: int
    db_filename: str
    # Token limits
    max_context_tokens: int
    summary_trigger_tokens: int
    runtime_window_tokens: int
    reserved_output_tokens: int

    @classmethod
    def from_env(cls) -> Self:
        max_recent_messages = int(environ.get("MAX_RECENT_MESSAGES", default="15"))
        summary_trigger_messages  = int(environ.get("SUMMARY_TRIGGER_MESSAGES", default="20"))
        db_filename = environ.get("DB_FILENAME", default="app.db")
        max_context_tokens = int(environ.get("MAX_CONTEXT_TOKENS", default="3000"))
        summary_trigger_tokens = int(environ.get("SUMMARY_TRIGGER_TOKENS", default="4000"))
        runtime_window_tokens = int(environ.get("RUNTIME_WINDOW_TOKENS", default="1500"))
        reserved_output_tokens = int(environ.get("RESERVED_OUTPUT_TOKENS", default="1000"))
        db_url = f"sqlite+aiosqlite:///{db_filename}"

        return cls(
            max_recent_messages=max_recent_messages,
            summary_trigger_messages=summary_trigger_messages,
            max_context_tokens=max_context_tokens,
            summary_trigger_tokens=summary_trigger_tokens,
            runtime_window_tokens=runtime_window_tokens,
            reserved_output_tokens=reserved_output_tokens,
            db_filename=db_url
        )

@lru_cache
def get_settings():
    return AppConfig.from_env()