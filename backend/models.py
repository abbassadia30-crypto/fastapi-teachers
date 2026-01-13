from .database import Base
from sqlalchemy import Column, Integer, String, Float,Boolean ,  JSON, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.sql import func

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
    role = Column(String, nullable=True)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    section = Column(String, nullable=False)
    fee = Column(Float, nullable=False)
    
    # Ownership: Email of the admin who admitted the student
    admitted_by = Column(String, index=True) 
    
    # Stores the flexible rows: {"Phone": "123", "Address": "Street 1"}
    extra_fields = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())