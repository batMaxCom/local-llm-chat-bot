from dataclasses import dataclass
from functools import lru_cache
from os import environ
from typing import Self


@dataclass(slots=True)
class AppConfig:
    db_filename: str

    @classmethod
    def from_env(cls) -> Self:
        db_filename = environ.get("DB_FILENAME", default="app.db")
        db_url = f"sqlite+aiosqlite:///{db_filename}"

        return cls(
            db_filename=db_url
        )

@lru_cache
def get_settings():
    return AppConfig.from_env()