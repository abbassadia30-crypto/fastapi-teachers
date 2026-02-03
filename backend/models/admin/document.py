import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, func, Float
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Syllabus(Base):
    __tablename__ = "Syllabus"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    name = Column(String, nullable=False)
    subject = Column(String)
    targets = Column(JSON)
    doc_type = Column(String)
    content = Column(JSON, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="syllabi")

class DateSheet(Base):
    __tablename__ = "datesheets"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    title = Column(String, nullable=False)
    target = Column(String, nullable=False)
    exams = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    institution = relationship("Institution", back_populates="datesheets")

class Notice(Base):
    __tablename__ = "institution_notices"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    language = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ADDED: Relationship back to Institution
    institution = relationship("Institution", back_populates="notices")

class VoucherMode(str, enum.Enum):
    student = "student"
    staff = "staff"

class FinanceTemplate(Base):
    __tablename__ = "finance_templates"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String, ForeignKey("institutions.institution_id"))
    target_group = Column(String)
    billing_month = Column(String)
    mode = Column(String)
    structure = Column(JSON)
    total_amount = Column(Float)
    issue_date = Column(String)
    due_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ADDED: Relationship back to Institution
    institution = relationship("Institution", back_populates="finance_templates")

class Transaction(Base):
    __tablename__ = "finance_transactions"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(String, ForeignKey("institutions.institution_id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("finance_templates.id"))
    amount = Column(Float)
    status = Column(String, default="unpaid")
    paid_at = Column(DateTime, nullable=True)
    voucher_no = Column(String, unique=True)

    # ADDED: Relationship back to Institution
    institution = relationship("Institution", back_populates="transactions")