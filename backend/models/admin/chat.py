from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Table, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin
import enum
from datetime import datetime

class ChatType(enum.Enum):
    ONE_TO_ONE = "one_to_one"
    SELECTIVE = "selective"
    BROADCAST = "broadcast"

# 🏛️ Association Table for Role-Based Participants
conversation_participants = Table(
    'conversation_participants',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('conversation_id', Integer, ForeignKey('conversations.id'), primary_key=True)
)

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=True)
    chat_type = Column(Enum(ChatType), default=ChatType.ONE_TO_ONE)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("User", secondary=conversation_participants)

class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    content = Column(Text, nullable=False)
    # 🏛️ Real App Features: Tracking delivery and read status
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)

    # Metadata for quick filtering without joining
    msg_type = Column(String, default="text") # text, image, file, voice

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")