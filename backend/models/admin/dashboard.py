import uuid
from sqlalchemy import Text

from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
from backend.models.base import Base

class student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    section = Column(String, nullable=False)
    fee = Column(Float, nullable=False)
    admitted_by = Column(String, index=True)
    extra_fields = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution = relationship("Institution", back_populates="student_records")

class teacher(Base):
    __tablename__ = "teacher_records"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject_expertise = Column(String)  # Specific to teachers
    phone = Column(String)
    salary = Column(Float)
    joining_date = Column(String)
    is_active = Column(Boolean, default=True)
    extra_details = Column(JSON, nullable=True)  # For those flexible fields

    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True)
    institution = relationship("Institution", back_populates="teacher_records")

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    cnic = Column(String, nullable=True)
    contact = Column(String, nullable=True)

    # This is perfect as is
    extra_details = Column(JSON, nullable=True, default={})

    institution_id = Column(Integer, ForeignKey("institutions.id"))

    institution = relationship("Institution", back_populates="staff_members")
