from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Owner(Base):
    __tablename__ = "owner"
    id = Column(Integer, primary_key=True)
    # Social/User Links
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_name = Column(String , ForeignKey('users.username'), nullable=False)
    email = Column(String , ForeignKey('users.email'), nullable=False)
    # Professional/Institution Link
    # Unique=True ensures an institution can only ever have ONE owner
    institution_id = Column(Integer, ForeignKey('institutions.id'), unique=True, nullable=False)
    institution_name = Column(String , ForeignKey('institutions.name'), nullable=False)
    # Relationships
    user = relationship("User", back_populates="owner_role")
    institution = relationship("Institution", back_populates="owner")

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    user_name = Column(String , ForeignKey('users.username'), nullable=False)
    email = Column(String , ForeignKey('users.email'), nullable=False)
    # Relationships
    user = relationship("User", back_populates="admin_role")
    institution = relationship("Institution", back_populates="admins")

class Teacher(Base):
    __tablename__ = "teacher"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    user_name = Column(String , ForeignKey('users.username'), nullable=False)
    email = Column(String , ForeignKey('users.email'), nullable=False)
    user = relationship("User", back_populates="teacher_role")
    institution = relationship("Institution", back_populates="teachers")

class Student(Base):
    __tablename__ = "student"
    id = Column(Integer, primary_key=True)
    user_name = Column(String , ForeignKey('users.username'), nullable=False)
    email = Column(String , ForeignKey('users.email'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    user = relationship("User", back_populates="student_role")
    institution = relationship("Institution", back_populates="students")
