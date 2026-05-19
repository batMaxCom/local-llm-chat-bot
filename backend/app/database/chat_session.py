from sqlalchemy import Column, UUID, String, Text, JSON
from sqlalchemy.orm import Mapped

from app.database.base import Base


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
