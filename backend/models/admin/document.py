import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, func, Float
from sqlalchemy.orm import relationship
from backend.models.admin.institution import Institution

from backend.database import Base

class Syllabus(Base):
    __tablename__ = "syllabi"
    name = Column(String, nullable=False)
    subject = Column(String)
    targets = Column(JSON)
    doc_type = Column(String)
    content = Column(JSON, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution = relationship("Institution", back_populates="syllabi")

class DateSheet(Base):
    __tablename__ = "datesheets"

    id = Column(Integer, primary_key=True, index=True)

    institution_id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)

    title = Column(String, nullable=False)
    target = Column(String, nullable=False)  # Class / Section / Program

    exams = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Notice(Base):
    __tablename__ = "institution_notices"

    id = Column(Integer, primary_key=True, index=True)

    institution_id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)

    title = Column(String, nullable=False)
    message = Column(String, nullable=False)

    language = Column(String, default="en")  # en / ur / ar
    is_active = Column(Boolean, default=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VoucherMode(str, enum.Enum):
    student = "student"
    staff = "staff"

class FinanceTemplate(Base):
    __tablename__ = "finance_templates"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    target_group = Column(String)
    billing_month = Column(String)
    mode = Column(String)
    structure = Column(JSON) # Stores list of heads
    total_amount = Column(Float)
    issue_date = Column(String)
    due_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Transaction(Base):
    __tablename__ = "finance_transactions"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("finance_templates.id"))
    amount = Column(Float)
    status = Column(String, default="unpaid")
    paid_at = Column(DateTime, nullable=True)
    voucher_no = Column(String, unique=True)