from resend import Contact
from sympy import true
from backend.database import Base
from sqlalchemy import Column, Integer, String, Float,Boolean ,  JSON, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    phone = Column(String, nullable=True) # Required for chat later
    password = Column(String)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, nullable=True)    
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    father_name = Column(String , nullable=False)
    section = Column(String, nullable=False)
    fee = Column(Float, nullable=False)
    admitted_by = Column(String, index=True) 
    extra_fields = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    


