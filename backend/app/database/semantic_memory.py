from sqlalchemy import Column, UUID, String, Text, DateTime, ForeignKey, Integer

from app.database.base import Base


class SemanticMemory(Base):
    __tablename__ = "semantic_memory"
    id = Column(Integer, primary_key=True)
    session_id = Column(UUID, ForeignKey("chat_session.id"), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
