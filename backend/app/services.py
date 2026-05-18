from typing import Any
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import ChatSession


class ChatSessionService:
    model = ChatSession

    async def add(self, session: AsyncSession, **values: Any):
        stmt = insert(self.model).values(**values)
        await session.execute(stmt)

    async def all(self, session: AsyncSession) -> list[dict]:
        stmt = select(self.model.id, self.model.title)
        rows = (await session.execute(stmt)).all()

        if rows:
            return [dict(row._mapping) for row in rows]
        return []

    async def one_only(self, session: AsyncSession, chat_id: UUID) -> ChatSession | None:
        stmt = select(self.model).where(self.model.id == chat_id)
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row:
            return row
        return None

    async def update_context(self, session: AsyncSession, chat_id: UUID, context: list[dict]) -> None:
        stmt = update(self.model).where(self.model.id == chat_id).values(context=context)
        await session.execute(stmt)

    async def update_summary(self, session: AsyncSession, chat_id: UUID, summary: str | None) -> None:
        stmt = update(self.model).where(self.model.id == chat_id).values(summary=summary)
        await session.execute(stmt)

    async def update_title(self, session: AsyncSession, chat_id: UUID, title: str) -> None:
        stmt = update(self.model).where(self.model.id == chat_id).values(title=title)
        await session.execute(stmt)
