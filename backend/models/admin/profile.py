from sqlalchemy import Text, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base

class UserBio(Base):
    __tablename__ = "user_bios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Personal info
    full_name = Column(String(100), nullable=False)
    short_bio = Column(Text, nullable=True)
    custom_details = Column(JSON, nullable=True, default={}) # Interests, Social Links

    # Matches: User.bio = relationship(..., back_populates="user_bio_link")
    user = relationship("User", back_populates="bio")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Professional/Institutional info
    professional_title = Column(String, index=True) # e.g., "Senior Administrator"
    office_hours = Column(String)
    institutional_bio = Column(Text) # Focused on their career/role
    extra_configs = Column(JSON) # Role-specific settings

    # Matches: User.profile = relationship(..., back_populates="profile_link")
    owner = relationship("User", back_populates="profile")