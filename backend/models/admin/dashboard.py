from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    name = Column(String)

    # ADDED: back-populating relationship to IndividualAttendance
    attendance_records = relationship("IndividualAttendance", back_populates="student")
    institution = relationship("Institution", back_populates="students")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    name = Column(String)

    institution = relationship("Institution", back_populates="staff_members")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    name = Column(String)

    institution = relationship("Institution", back_populates="teachers")
