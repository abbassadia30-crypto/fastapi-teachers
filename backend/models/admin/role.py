import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, func, Float, Date
from sqlalchemy.orm import relationship, foreign
from backend.models.base import Base

class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True)
    username = Column(String , ForeignKey('user.username'))
    email = Column(String, ForeignKey("users.email"), ondelete='CASCADE')
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institution.id"))
    institution_name = Column(String, ForeignKey("institution.name"))

    institution = relationship("Institution", back_populates="admin")
    user = relationship("User", back_populates="admin")

class Teacher(Base):
    __tablename__ = 'teacher'
    id = Column(Integer, primary_key=True)
    username = Column(String , ForeignKey('user.username'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institution.id"))
    institution_name = Column(String, ForeignKey("institution.name"))

    user = relationship("User", back_populates="teacher")
    institution = relationship("Institution", back_populates="teacher")

class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    username = Column(String , ForeignKey('user.username'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institution.id"))
    institution_name = Column(String, ForeignKey("institution.name"))

    user = relationship("User", back_populates="student")
    institution = relationship("Institution", back_populates="student")