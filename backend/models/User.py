from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

# --- SHARED BASE FOR DATA ---
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True, nullable=False)
    user_email = Column(String, unique=True, index=True, nullable=False)
    user_password = Column(String, nullable=False)
    type = Column(String(50)) # Discriminator
    phone = Column(String, nullable=True)

    # Inside the User Class
    bio = relationship("UserBio", back_populates="user", uselist=False)

# REMOVED: profile = relationship("Profile", ...)
# Because a user might have 3 different profiles for 3 different roles.

    @property
    def active_profile(self):
      """Logic to fetch the profile of the current active role"""
      if self.type == "owner" and self.owner: return self.owner.profile
      if self.type == "admin" and self.admin: return self.admin.profile
      if self.type == "teacher" and self.teacher: return self.teacher.profile
      if self.type == "student" and self.student: return self.student.profile
      return None

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
    }

# --- SPECIFIC ROLES ---

class Owner(User):
    __tablename__ = "owner"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), unique=True, nullable=False)

    # Role-Specific Data
    profile = relationship("Profile", back_populates="owner_role", uselist=False,
                       foreign_keys="Profile.owner_id") # Explicitly link to owner_id
    institution = relationship("Institution", back_populates="owner")

    __mapper_args__ = {"polymorphic_identity": "owner"}

class Admin(User):
    __tablename__ = "admin"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    # Role-Specific Data
    profile = relationship("Profile", back_populates="admin_role", uselist=False,
                       foreign_keys="Profile.admin_id") # Explicitly link to admin_id
    institution = relationship("Institution", back_populates="admins")

    __mapper_args__ = {"polymorphic_identity": "admin"}

class Teacher(User):
    __tablename__ = "teacher"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    # Role-Specific Data
    profile = relationship("Profile", back_populates="teacher_role", uselist=False,
                       foreign_keys="Profile.teacher_id") # Explicitly link to teacher_id
    institution = relationship("Institution", back_populates="teachers")

    __mapper_args__ = {"polymorphic_identity": "teacher"}

class Student(User):
    __tablename__ = "student"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    # Role-Specific Data
    profile = relationship("Profile", back_populates="student_role", uselist=False,
                       foreign_keys="Profile.student_id") # Explicitly link to student_id
    institution = relationship("Institution", back_populates="students")

    __mapper_args__ = {"polymorphic_identity": "student"}

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
