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
    phone = Column(String, nullable=True)
    type = Column(String(50))

    # Removed: owner_role, admin_role, etc.
    # Inheritance handles this! If user.type is 'admin',
    # SQLAlchemy treats the object as an Admin automatically.

    bio = relationship("UserBio", back_populates="user", uselist=False)

    @property
    def institution_id(self):
        """Logic to find the ID without crashing.
        Because of inheritance, 'self' will actually be an instance
        of Owner, Admin, etc., if it's already loaded."""
        # This is high-end: check if the attribute exists on the current object
        return getattr(self, "institution_id", None)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
    }

class Owner(User):
    __tablename__ = "owner"
    # Shared Primary Key with User table
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), unique=True, nullable=False)

    # We only define the relationship to the INSTITUTION here
    institution = relationship("Institution", back_populates="owner")

    __mapper_args__ = {
        "polymorphic_identity": "owner",
    }

class Admin(User):
    __tablename__ = "admin"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    institution = relationship("Institution", back_populates="admins")

    __mapper_args__ = {
        "polymorphic_identity": "admin",
    }

class Teacher(User):
    __tablename__ = "teacher"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    department = Column(String(100), nullable=True)

    institution = relationship("Institution", back_populates="teachers")

    __mapper_args__ = {
        "polymorphic_identity": "teacher",
    }

class Student(User):
    __tablename__ = "student"
    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    roll_number = Column(String(50), nullable=True)

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
