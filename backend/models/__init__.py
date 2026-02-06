# backend/models/__init__.py

# 1. Get the single Base
from .base import Base

# 2. Import all models to make them visible to SQLAlchemy
from .admin.institution import Institution, School, Academy, College, User
from .admin.profile import UserBio, Profile
from .admin.document import (
    Syllabus, DateSheet, Notice, Transaction,
    FinanceTemplate, Voucher, AcademicResult, PaperVault,
    AttendanceLog, IndividualAttendance
)
from .admin.dashboard import Student, Staff, Teacher
# CORRECTED: Added the import for the new Message model
from .admin.chat import Message
from .admin.role import Admin , student , teacher
# Ensure all are available for main.py
__all__ = [
    "Base", "User", "Institution", "Syllabus",
    "School", "Academy", "College", "UserBio",
    "Profile", "DateSheet", "Notice", "Transaction",
    "FinanceTemplate", "Student", "Staff", "Teacher",
    "Voucher", "AcademicResult", "PaperVault",
    "AttendanceLog", "IndividualAttendance",
    "Message" , "Admin" , "teacher", "student"
]
