from typing import AsyncGenerator, Any

from sqlalchemy import Column, UUID, String, JSON, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped

from app.configs import get_settings
from app.memory import SYSTEM_PROMPT

settings = get_settings()
engine = create_async_engine(settings.db_filename)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
        finally:
            await session.commit()

class ChatSession(Base):
    __tablename__ = "chat_session"
    id = Column('id', UUID(as_uuid=True), primary_key=True)
    title = Column('title', String, nullable=None, default=None)
    summary = Column('summary', Text(), nullable=True, default=None)
    context: Mapped[list] = Column(
        'context',
        JSON,
        nullable=False,
        default=[]
    )
