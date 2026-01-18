import enum
import uuid
from pydantic import EmailStr
from regex import T
from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sympy import true
from backend.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# ... (Previous imports)
class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    institution_code = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4().hex[:8].upper()))
    type = Column(String(50)) 
    name = Column(String, nullable=False)
    address = Column(String)
    email = Column(String)

    # FIX: Explicitly tell SQLAlchemy which FK to use for the owner
    owner = relationship("User", back_populates="owned_institution", foreign_keys=[owner_id])
    students = relationship("Student", back_populates="institution")

    __mapper_args__ = {"polymorphic_identity": "institution", "polymorphic_on": type}

class Student(Base):
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
    institution = relationship("Institution", back_populates="students")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student")
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # This is for staff/teachers who belong to an institution
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    
    # FIX: Separate 'the institution I own' from 'the institution I work for'
    # This relationship represents the school the user OWNED
    owned_institution = relationship("Institution", back_populates="owner", foreign_keys="[Institution.owner_id]", uselist=False)
    
    # This relationship represents the school the user belongs to (Staff/Teacher)
    employed_at = relationship("Institution", foreign_keys=[institution_id])
# --- Specific Institution Types ---

class School(Institution):
    __tablename__ = "schools"
    # Link back to the parent ID
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    principal_name = Column(String)
    campus = Column(String)
    website = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "school",
    }

class Academy(Institution):
    __tablename__ = "academies"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    edu_type = Column(String)
    campus_name = Column(String)
    contact = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "academy",
    }

class College(Institution):
    __tablename__ = "colleges"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    dean_name = Column(String)
    code = Column(String)
    uni = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "college",
    }

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class Staff(Base):
    __tablename__ = "staff_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    designation = Column(String) # Teacher, Accountant, Driver, etc.
    phone = Column(String)
    salary = Column(Float)
    joining_date = Column(String) 
    # This ensures only the Admin who hired them can see them
    institution_id = Column(Integer, ForeignKey("institutions.id") , index=True)
    is_active = Column(Boolean, default=True)
    # This stores "Excel-like" extra data (JSON)
    extra_details = Column(JSON, nullable=True)
   