import uuid
from sqlalchemy import Text, Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    internal_id = Column(String, unique=True, index=True, nullable=False,
                         default=lambda: str(uuid.uuid4().hex[:8].upper()))

    type = Column(String(50))
    name = Column(String, nullable=False)
    address = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)

    inst_ref = Column(String(8), unique=True, index=True, nullable=False)
    join_key = Column(String(10), unique=True, nullable=False)

    # 👑 THE CORE ROLES
    # Note: 'foreign_keys' is used to resolve the ambiguity from the previous error.
    owner = relationship("Owner", back_populates="institution", uselist=False,
                         foreign_keys="Owner.institution_id")

    admins = relationship("Admin", back_populates="institution",
                          foreign_keys="Admin.institution_id")

    teachers = relationship("Teacher", back_populates="institution",
                            foreign_keys="Teacher.institution_id")

    students = relationship("Student", back_populates="institution",
                            foreign_keys="Student.institution_id")

    # 📑 RECORDS & LOGS (Dashboard Models)
    # Ensure 'student' and 'teacher' (lowercase) are correctly mapped in those files
    student_records = relationship("student", back_populates="institution")
    teacher_records = relationship("teacher", back_populates="institution")
    staff_members = relationship("Staff", back_populates="institution")
    syllabi = relationship("Syllabus", back_populates="institution")
    datesheets = relationship("DateSheet", back_populates="institution")
    notices = relationship("Notice", back_populates="institution")
    finance_templates = relationship("FinanceTemplate", back_populates="institution")
    transactions = relationship("Transaction", back_populates="institution")
    vouchers = relationship("Voucher", back_populates="institution")
    academic_results = relationship("AcademicResult", back_populates="institution")
    papers = relationship("PaperVault", back_populates="institution")
    attendance_logs = relationship("AttendanceLog", back_populates="institution")
    individual_attendances = relationship("IndividualAttendance", back_populates="institution")


    __mapper_args__ = {"polymorphic_identity": "institution", "polymorphic_on": type}

class School(Institution):
    __tablename__ = "schools"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    principal_name = Column(String)
    campus = Column(String)
    website = Column(String)
    __mapper_args__ = {"polymorphic_identity": "school"}

class Academy(Institution):
    __tablename__ = "academies"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    edu_type = Column(String)
    campus_name = Column(String)
    contact = Column(String)
    __mapper_args__ = {"polymorphic_identity": "academy"}

class College(Institution):
    __tablename__ = "colleges"
    id = Column(Integer, ForeignKey("institutions.id"), primary_key=True)
    dean_name = Column(String)
    code = Column(String)
    uni = Column(String)
    __mapper_args__ = {"polymorphic_identity": "college"}
