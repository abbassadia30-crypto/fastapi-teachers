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

    # FIX: Added primaryjoin to handle multiple Foreign Keys to 'institutions'
    institution = relationship(
        "Institution",
        primaryjoin="Admin.institution_id == Institution.id",
        foreign_keys=[institution_id],
        back_populates="admin"
    )
    user = relationship("User", foreign_keys=[user_id], back_populates="admin")

class teacher(Base):
    __tablename__ = 'teacher_roles'
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.name'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution_name = Column(String, ForeignKey("institutions.name"))

    user = relationship("User", foreign_keys=[user_id], back_populates="teacher_role")

    # FIX: Added primaryjoin
    institution = relationship(
        "Institution",
        primaryjoin="teacher.institution_id == Institution.id",
        foreign_keys=[institution_id],
        back_populates="teacher_roles"
    )

class student(Base):
    __tablename__ = 'student_roles'
    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('users.name'))
    email = Column(String, ForeignKey("users.email"))
    user_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution_name = Column(String, ForeignKey("institutions.name"))

    user = relationship("User", foreign_keys=[user_id], back_populates="student_role")

    # FIX: Added primaryjoin
    institution = relationship(
        "Institution",
        primaryjoin="student.institution_id == Institution.id",
        foreign_keys=[institution_id],
        back_populates="student_roles"
    )