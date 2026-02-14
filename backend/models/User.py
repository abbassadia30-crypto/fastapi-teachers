from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    phone = Column(String , nullable=False)
    type = Column(String(50))

    owner_role = relationship("Owner", back_populates="user", foreign_keys="[Owner.user_id]", uselist=False)
    admin_role = relationship("Admin", back_populates="user", foreign_keys="[Admin.user_id]", uselist=False)
    teacher_role = relationship("Teacher", back_populates="user", foreign_keys="[Teacher.user_id]", uselist=False)
    student_role = relationship("Student", back_populates="user", foreign_keys="[Student.user_id]", uselist=False)

    bio = relationship("UserBio", back_populates="user", uselist=False)
    profile = relationship("Profile", back_populates="owner", uselist=False)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
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
