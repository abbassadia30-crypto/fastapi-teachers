# backend/models/__init__.py

# --- 1. Core Imports ---
from .base import Base
from .admin.institution import Institution, School, Academy, College, User
from .admin.chat import Message

# --- 2. Dependent Model Imports ---
from .admin.profile import UserBio, Profile
from .admin.document import (
    Syllabus, DateSheet, Notice, Transaction, 
    FinanceTemplate, Voucher, AcademicResult, PaperVault, 
    AttendanceLog, IndividualAttendance
)
# CORRECTED: Importing the uppercase classes from dashboard
from .admin.dashboard import Staff, Student, Teacher
# CORRECTED: Importing the new lowercase role classes
from .admin.role import Admin, student, teacher

# --- 3. All Exports ---
__all__ = [
    "Base", "User", "Institution", "Message",
    "School", "Academy", "College", "UserBio",
    "Profile", "Syllabus", "DateSheet", "Notice", 
    "Transaction", "FinanceTemplate", "Voucher", 
    "AcademicResult", "PaperVault", "AttendanceLog", 
    "IndividualAttendance",
    # CORRECTED: Exposing both sets of classes
    "Student", "Staff", "Teacher",
    "Admin", "student", "teacher"
]
