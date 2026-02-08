from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    user_email = Column(String, unique=True, index=True, nullable=False)
    user_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user"
    }

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

