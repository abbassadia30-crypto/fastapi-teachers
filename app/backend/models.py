from sqlalchemy import Column, Integer, String
from app.backend.database import Base

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True)
    student_name = Column(String, nullable=False)
    father_name = Column(String)
    phone = Column(String)
    father_cnic = Column(String)
    grade = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    password = Column(String)