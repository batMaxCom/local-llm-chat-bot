from datetime import datetime, UTC

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.database.semantic_memory import SemanticMemory
from app.semantic.schemas import (
    SemanticFact,
)


class SemanticMemoryService:

    model = SemanticMemory

    async def save_facts(
        self,
        session: AsyncSession,
        session_id: str,
        facts: list[SemanticFact],
    ) -> None:
        existing_facts = await self.get_facts(
            session=session,
            session_id=session_id,
        )

        existing_contents = {
            fact.content.lower()
            for fact in existing_facts
        }

        for fact in facts:
            normalized = (
                fact.content.lower().strip()
            )

            if normalized in existing_contents:
                continue

            session.add(
                SemanticMemory(
                    session_id=session_id,
                    category=fact.category,
                    content=fact.content,
                    created_at=datetime.now(UTC)
                )
            )

        await session.commit()

    async def get_facts(
        self,
        session: AsyncSession,
        session_id: str,
    ) -> list[SemanticMemory]:
        result = await session.execute(
            select(self.model)
            .where(
                self.model.session_id
                == session_id
            )
        )

        return list(
            result.scalars().all()
        )


    async def get_recent_facts(
        self,
        session: AsyncSession,
        session_id: str,
        limit: int = 10,
    ) -> list[SemanticMemory]:
        result = await session.execute(
            select(self.model)
            .where(
                self.model.session_id
                == session_id
            )
            .order_by(
                desc(
                    self.model.created_at
                )
            )
            .limit(limit)
        )

        return list(
            result.scalars().all()
        )