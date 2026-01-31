import uuid
from sqlalchemy import Text

from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass


class UserBio(Base):
    __tablename__ = "user_bios"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    short_bio = Column(Text, nullable=True)
    custom_details = Column(JSON, nullable=True, default={})
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # This matches the 'bio' property we just added to User
    user = relationship("User", back_populates="bio")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, index=True)
    short_bio = Column(Text)
    custom_details = Column(JSON)
    owner = relationship("User", back_populates="profile")