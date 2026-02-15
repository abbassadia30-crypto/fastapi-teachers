import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, func, Float, Date
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Syllabus(Base):
    __tablename__ = "Syllabus"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)
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
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)
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
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    language = Column(String, default="en")
    is_active = Column(Boolean, default=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    institution = relationship("Institution", back_populates="notices")

class VoucherMode(str, enum.Enum):
    student = "student"
    staff = "staff"

class FinanceTemplate(Base):
    __tablename__ = "finance_templates"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    target_group = Column(String)
    billing_month = Column(String)
    mode = Column(String)
    structure = Column(JSON)
    total_amount = Column(Float)
    issue_date = Column(String)
    due_date = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="finance_templates")

class Transaction(Base):
    __tablename__ = "finance_transactions"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    template_id = Column(Integer, ForeignKey("finance_templates.id"))
    amount = Column(Float)
    status = Column(String, default="unpaid")
    paid_at = Column(DateTime, nullable=True)
    voucher_no = Column(String, unique=True)

    institution = relationship("Institution", back_populates="transactions")

class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    recipient_type = Column(String)
    name = Column(String, nullable=False)
    registration_id = Column(String)
    father_name = Column(String)
    phone = Column(String)

    billing_period = Column(String)
    particulars = Column(JSON)
    total_amount = Column(Float)

    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)

    institution = relationship("Institution", back_populates="vouchers")

class AcademicResult(Base):
    __tablename__ = "academic_results"

    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)

    exam_title = Column(String, nullable=False)
    target_class = Column(String)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=True)
    student_name = Column(String, nullable=False)
    father_name = Column(String)
    marks_data = Column(JSON)
    percentage = Column(Float)
    final_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)

    institution = relationship("Institution", back_populates="academic_results")

class PaperVault(Base):
    __tablename__ = "paper_vault"

    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    subject = Column(String, nullable=False)
    target_class = Column(String)
    paper_type = Column(String)
    duration = Column(String)
    language = Column(String, default="en")
    content_blueprint = Column(JSON)
    total_marks = Column(Integer)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)

    institution = relationship("Institution", back_populates="papers")

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    section_identifier = Column(String, index=True)
    custom_section_name = Column(String, nullable=True)
    log_date = Column(Date, index=True)
    category = Column(String)
    subject = Column(String, nullable=True)
    is_official = Column(Boolean, default=True)
    attendance_data = Column(JSON)
    p_count = Column(Integer, default=0)
    a_count = Column(Integer, default=0)
    l_count = Column(Integer, default=0)

    institution = relationship("Institution", back_populates="attendance_logs")

class IndividualAttendance(Base):
    __tablename__ = "individual_attendance"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey("student.id"), index=True)
    log_id = Column(Integer, ForeignKey("attendance_logs.id"))
    status = Column(String)
    date = Column(Date, index=True)

    student = relationship("Student")
    parent_log = relationship("AttendanceLog")
    institution = relationship("Institution", back_populates="individual_attendances")
