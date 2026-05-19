from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UUID

from app.database.base import Base


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    session_id = Column(UUID, ForeignKey("chat_session.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
