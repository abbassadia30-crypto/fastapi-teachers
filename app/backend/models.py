from sqlalchemy import Column, Integer, String
from app.backend.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # Added name field for better admin profiles
    name = Column(String(100), nullable=True) 
    email = Column(String(100), unique=True, index=True)
    password = Column(String(100))

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(50), unique=True, index=True)
    student_name = Column(String(100), nullable=False)
    father_name = Column(String(100) , nullable=True)
    phone = Column(String(20))
    father_cnic = Column(String(20))
    grade = Column(String(50))
    fees = Column(Integer, default=0)
    created_by = Column(String(100), index=True, nullable=True)