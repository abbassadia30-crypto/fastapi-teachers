from sqlalchemy import Column, Integer, String, Boolean
from app.backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) 
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255)) # Increased length for hashed passwords
    # --- REAL APP ADDITIONS ---
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(10), nullable=True)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(50), unique=True, index=True)
    student_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=False) # Changed to False for better records
    phone = Column(String(20), nullable=False)        # Changed to False for contactability
    father_cnic = Column(String(20), nullable=True)   # Keep nullable as discussed
    grade = Column(String(50), nullable=False)
    fees = Column(Integer, default=0, nullable=False)
    created_by = Column(String(100), index=True, nullable=False)