from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Table, Boolean, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin
import enum

class ChatType(enum.Enum):
    ONE_TO_ONE = "one_to_one"
    SELECTIVE = "selective"  # Group/Class
    BROADCAST = "broadcast"  # One-to-All

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=True) # Name of group (e.g., "Physics Class A")
    chat_type = Column(Enum(ChatType), default=ChatType.ONE_TO_ONE)

    # Professional Scope: Link to the Institution
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("User", secondary="conversation_participants")

    conversation_participants = Table(
        'conversation_participants',
        Base.metadata,
        Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
        Column('conversation_id', Integer, ForeignKey('conversations.id'), primary_key=True)
    )

class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")