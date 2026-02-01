import uuid
from sqlalchemy import Text

from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
from backend.models.base import Base

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(String, unique=True, index=True, nullable=False,
                            default=lambda: str(uuid.uuid4().hex[:8].upper()))
    type = Column(String(50))
    name = Column(String, nullable=False)
    address = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    owner = relationship("User", back_populates="owned_institution", foreign_keys=[owner_id])
    students = relationship("Student", back_populates="institution")
    staff_members = relationship("Staff", back_populates="institution")
    teachers = relationship("Teacher", back_populates="institution")

    # 🏛️ PEER TIP: Ensure "Syllabus" matches the CLASS name in syllabus.py exactly
    syllabi = relationship("Syllabus", back_populates="institution")

    __mapper_args__ = {"polymorphic_identity": "institution", "polymorphic_on": type}

class School(Institution):
    __tablename__ = "schools"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    principal_name = Column(String)
    campus = Column(String)
    website = Column(String)
    __mapper_args__ = {"polymorphic_identity": "school"}

class Academy(Institution):
    __tablename__ = "academies"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    edu_type = Column(String)
    campus_name = Column(String)
    contact = Column(String)
    __mapper_args__ = {"polymorphic_identity": "academy"}

class College(Institution):
    __tablename__ = "colleges"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    dean_name = Column(String)
    code = Column(String)
    uni = Column(String)
    __mapper_args__ = {"polymorphic_identity": "college"}

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="unassigned")# Set to None/Null for onboarding later
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)
    has_institution = Column(Boolean, default=False)
    institution_id = Column(Integer, ForeignKey("institutions.id") , nullable=True)

    bio = relationship("UserBio", back_populates="user", uselist=False)
    owned_institution = relationship("Institution", back_populates="owner",
                                     foreign_keys=[Institution.owner_id], uselist=False)
    profile = relationship("Profile", back_populates="owner", uselist=False)
    employed_at = relationship("Institution", foreign_keys=[institution_id])