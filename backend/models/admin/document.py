from datetime import datetime

from sqlalchemy import Column, Integer, String, JSON, Float,ForeignKey, DateTime, Boolean , Enum ,Date
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
from backend.models.base import Base
import enum

class Syllabus(Base):
    __tablename__ = "Syllabus"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    name = Column(String, nullable=False) # e.g., "Physics Syllabus - Grade 10"
    doc_type = Column(String) # syllabus, exam, translate, or scan
    content = Column(JSON, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    institution = relationship("Institution")

class DateSheet(Base):
    __tablename__ = "datesheets"

    id = Column(Integer, primary_key=True, index=True)

    institution_ref = Column(String, ForeignKey("institutions.institution_id"))

    title = Column(String, nullable=False)
    target = Column(String, nullable=False)  # Class / Section / Program

    exams = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notice(Base):
    __tablename__ = "institution_notices"

    id = Column(Integer, primary_key=True, index=True)

    institution_ref = Column(String, ForeignKey("institutions.institution_id"))

    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    language = Column(String, default="en")  # en / ur / ar
    is_active = Column(Boolean, default=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VoucherMode(str, enum.Enum):
    student = "student"
    staff = "staff"

class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    # Every voucher must belong to a specific institution
    institution_id = Column(String, ForeignKey("institutions.institution_id"), nullable=False)

    target_group = Column(String, nullable=False)
    billing_month = Column(String, nullable=False)  # YYYY-MM
    mode = Column(Enum(VoucherMode), nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    total_amount = Column(Float, nullable=False)

    # Relationships
    heads = relationship("VoucherHead", back_populates="voucher", cascade="all, delete")

class VoucherHead(Base):
    __tablename__ = "voucher_heads"

    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"))

    # Redundant but useful for high-speed queries without joins
    institution_id = Column(String, ForeignKey("institutions.institution_id"), nullable=False)

    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

    voucher = relationship("Voucher", back_populates="heads")