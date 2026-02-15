from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True, nullable=False)
    user_email = Column(String, unique=True, index=True, nullable=False)
    user_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    phone = Column(String , nullable=True)
    type = Column(String(50))

# Inside the User class
    owner_role = relationship("Owner", back_populates="user", foreign_keys="Owner.id", uselist=False)
    admin_role = relationship("Admin", back_populates="user", foreign_keys="Admin.id", uselist=False)
    teacher_role = relationship("Teacher", back_populates="user", foreign_keys="Teacher.id", uselist=False)
    student_role = relationship("Student", back_populates="user", foreign_keys="Student.id", uselist=False)

    bio = relationship("UserBio", back_populates="user", uselist=False)
    profile = relationship("Profile", back_populates="owner", uselist=False)

    @property
    def institution_id(self):
        """Logic to find the ID without crashing"""
        if self.type == "owner" and self.owner_role:
            return self.owner_role.institution_id
        if self.type == "admin" and self.admin_role:
            return self.admin_role.institution_id
        if self.type == "teacher" and self.teacher_role:
            return self.teacher_role.institution_id
        if self.type == "student" and self.student_role:
            return self.student_role.institution_id
        return None

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
    }

class Owner(User): # Inherit from User, not Base
    __tablename__ = "owner"
    # id here acts as both PK and FK to users.id
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), unique=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="owner_role", foreign_keys=[id])
    institution = relationship("Institution", back_populates="owner")

    __mapper_args__ = {
        "polymorphic_identity": "owner",
    }

# --- ADMIN ROLE (Joined Table) ---
class Admin(User): # Inherit from User, not Base
    __tablename__ = "admin"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    user = relationship("User", back_populates="admin_role", foreign_keys=[id])
    institution = relationship("Institution", back_populates="admins")

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

# backend/models/admin/role.py

class Teacher(User):
    __tablename__ = "teacher"
    # The 'id' is both the Primary Key for this table
    # and a Foreign Key to the 'users' table id.
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    # High-end addition: Specialization or Department for Teachers
    department = Column(String(100), nullable=True)

    user = relationship("User", back_populates="teacher_role", foreign_keys=[id])
    institution = relationship("Institution", back_populates="teachers")

    __mapper_args__ = {
        "polymorphic_identity": "teacher",
    }

class Student(User):
    __tablename__ = "student"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    # Student specific data
    roll_number = Column(String(50), nullable=True)

    user = relationship("User", back_populates="student_role", foreign_keys=[id])
    institution = relationship("Institution", back_populates="students")

    __mapper_args__ = {
        "polymorphic_identity": "student",
    }

class UserBan(Base, TimestampMixin):
    __tablename__ = "user_bans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # We use ban_count to track history; it shouldn't be a primary key
    ban_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)

class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)

    # Who is reporting?
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Who is being reported?
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    reason = Column(Text, nullable=False)
    evidence_link = Column(String, nullable=True) # Optional link to a screenshot

class Block(Base, TimestampMixin):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)

    # The person doing the blocking
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The person being blocked
    blocked_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Logic: "user" (personal block) or "institution" (banned from school/college)
    block_type = Column(String, default="user")

    # If block_type is 'institution', we need to know which one
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)

class Verification(User):
    __tablename__ = "verification"

    # In Joined Inheritance, this ID is the link to the User table
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    otp_code = Column(String, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "verified_user"
    }
