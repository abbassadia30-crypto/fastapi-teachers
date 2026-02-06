from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class Message(Base):
    __tablename__ = "Message"
    id = Column(Integer, primary_key=True)
    content = Column(String)
    message_type = Column(String, default="text")

    # 🔗 Direct link to the Institution
    institution_id = Column(Integer, ForeignKey('institution.id'), index=True)

    # Flags (using lowercase 'default')
    is_read = Column(Boolean, default=False)
    is_seen = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    sent_at_day = Column(String)
    sent_at_month = Column(String)
    sent_at_year = Column(String)

    # Participants
    sender = Column(String)
    sender_id = Column(Integer, ForeignKey('user.id'))
    receiver = Column(String)
    receiver_id = Column(Integer) # ID of the recipient user

    # Metadata
    deleted_at = Column(DateTime, nullable=True)
    replied_by = Column(String, nullable=True)
    replied_at = Column(DateTime, nullable=True)

    # Relationships
    # Link to the institution record
    institution = relationship("Institution", back_populates="messages")
    # Link to the sender user
    user = relationship("User", back_populates="messages")