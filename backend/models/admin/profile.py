from sqlalchemy import Text, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base

class UserBio(Base):
    __tablename__ = "user_bios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True) # Personal info is 1-to-1 with the Human

    full_name = Column(String(100), nullable=False)
    short_bio = Column(Text, nullable=True)
    custom_details = Column(JSON, nullable=True, default={})

    user = relationship("User", back_populates="bio")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id")) # No unique=True; one user, many roles

    # Discriminator to know which role this profile represents
    role_type = Column(String(50)) # 'owner', 'admin', 'teacher', 'student'
    institution_id = Column(Integer, ForeignKey("institutions.id"))

    # Professional info
    professional_title = Column(String, index=True)
    office_hours = Column(String)
    institutional_bio = Column(Text)
    extra_configs = Column(JSON)

    # Link back to the user
    owner = relationship("User", back_populates="profiles")