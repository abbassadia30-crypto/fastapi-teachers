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

# backend/models/admin/profile.py

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)

    # Data Fields
    professional_title = Column(String, index=True)
    office_hours = Column(String)
    institutional_bio = Column(Text)
    extra_configs = Column(JSON)

    # Foreign Keys to the specific role tables
    owner_id = Column(Integer, ForeignKey('owner.id'), nullable=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=True)
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=True)

    # Relationship partners (Matches the 'profile' var in Role classes)
    owner_role = relationship("Owner", back_populates="profile")
    admin_role = relationship("Admin", back_populates="profile")
    teacher_role = relationship("Teacher", back_populates="profile")
    student_role = relationship("Student", back_populates="profile")