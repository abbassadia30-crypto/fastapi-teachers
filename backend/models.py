from sqlalchemy import Column, Integer, String, Boolean
from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    # This field is required for the 1-minute logic
    otp_created_at = Column(DateTime, default=datetime.utcnow)

class StudentRecord(Base):
    __tablename__ = "student_records"
    student_name = Column(String , nullable=False)
    father_name = Column(String , nullable=False)
    Father_cnic = Column(String , nullable=True)
    phone = Column(Integer , nullable=False)
    grade = Column(String , nullable=False)
    fees = Column(Integer , nullable=False)