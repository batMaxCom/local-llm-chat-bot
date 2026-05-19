import math
from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import insert, select, Select, func, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.message import Message


class MessageService:
    model = Message

    @staticmethod
    def _add_query_offset_and_limit(
        query: Select, offset: int, limit: int
    ) -> Select:
        """Смещение и ограничение запроса."""
        offset = offset - 1 if offset > 0 else offset
        return query.offset(offset * limit).limit(limit)

    @staticmethod
    def model_to_dict(obj):
        return {
            c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs
        }

    async def add(
            self,
            session: AsyncSession,
            session_id: UUID,
            role: str,
            content: str
    ) -> None:
        stmt = insert(self.model).values(
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.now(UTC)
        )
        await session.execute(stmt)

    async def load_only(self):
        ...

    async def  load_paginated(
            self,
            session: AsyncSession,
            session_id: UUID,
            before_id: int | None = None,
            limit: int = 20
    ) -> dict:
        stmt = (
            select(self.model)
            .where(self.model.session_id == session_id)
        )

        if before_id:
            stmt = stmt.where(self.model.id < before_id)

        stmt = (
            stmt.order_by(self.model.id.desc())
            .limit(limit)
        )

        rows = (await session.execute(stmt)).scalars().all()

        rows.reverse()

        return [self.model_to_dict(row) for row in rows]
