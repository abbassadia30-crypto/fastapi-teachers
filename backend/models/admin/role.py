from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Admin(Base):
    __tablename__ = 'admin'
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.name'))
    email = Column(String, ForeignKey("users.email", ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution_name = Column(String, ForeignKey("institutions.name"))

    institution = relationship("Institution", foreign_keys=[institution_id], back_populates="admin")
    user = relationship("User", foreign_keys=[user_id], back_populates="admin")

# CORRECTED: Class names are now lowercase to avoid conflicts
class teacher(Base):
    __tablename__ = 'teacher_roles' # Renamed table to avoid conflict with 'teacher' table from dashboard
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.name'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution_name = Column(String, ForeignKey("institutions.name"))

    user = relationship("User", foreign_keys=[user_id], back_populates="teacher_role")
    institution = relationship("Institution", foreign_keys=[institution_id], back_populates="teacher_roles")

class student(Base):
    __tablename__ = 'student_roles' # Renamed table to avoid conflict with 'student' table from dashboard
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.name'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution_name = Column(String, ForeignKey("institutions.name"))

    user = relationship("User", foreign_keys=[user_id], back_populates="student_role")
    institution = relationship("Institution", foreign_keys=[institution_id], back_populates="student_roles")
