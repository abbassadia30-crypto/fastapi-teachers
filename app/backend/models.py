from sqlalchemy import Column, Integer, String
from app.backend.database import Base, engine

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, nullable=True)
    student_name = Column(String, nullable=False)
    father_name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    father_cnic = Column(String , nullable=False)
    grade = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)