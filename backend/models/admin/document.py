from datetime import datetime

from sqlalchemy import Column, Integer, String, JSON, Float,ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
from backend.models.base import Base


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

class FinanceTemplate(Base):
    __tablename__ = "finance_templates"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    target_group = Column(String)  # e.g., "Grade 10-A"
    billing_month = Column(String) # e.g., "2026-02"
    mode = Column(String)          # "student" or "staff"
    # Stores heads like [{"name": "Tuition", "amount": 5000}]
    structure = Column(JSON)
    total_amount = Column(Float)
    issue_date = Column(String)
    due_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Transaction(Base):
    __tablename__ = "finance_transactions"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    user_id = Column(Integer, ForeignKey("users.id")) # Link to Student or Staff
    template_id = Column(Integer, ForeignKey("finance_templates.id"))
    amount = Column(Float)
    status = Column(String, default="unpaid") # unpaid, paid, partial
    paid_at = Column(DateTime, nullable=True)
    voucher_no = Column(String, unique=True) # e.g., "INV-2026-001"

