# backend/models/__init__.py

# --- 1. Core Imports ---
# Import the declarative base first.
from .base import Base

# Import the core models that everything else depends on.
from .admin.institution import Institution, School, Academy, College, User
from .admin.chat import Message

# --- 2. Dependent Model Imports ---
# Import all other models that have relationships to the core models.
from .admin.profile import UserBio, Profile
from .admin.document import (
    Syllabus, DateSheet, Notice, Transaction, 
    FinanceTemplate, Voucher, AcademicResult, PaperVault, 
    AttendanceLog, IndividualAttendance
)
from .admin.dashboard import Staff # Student and Teacher are in role.py

# CORRECTED: Casing for class names must be correct (Student, Teacher)
from .admin.role import Admin, Student, Teacher

# --- 3. All Exports ---
# Define what is exported from this package.
__all__ = [
    "Base", "User", "Institution", "Message",
    "School", "Academy", "College", "UserBio",
    "Profile", "Syllabus", "DateSheet", "Notice", 
    "Transaction", "FinanceTemplate", "Voucher", 
    "AcademicResult", "PaperVault", "AttendanceLog", 
    "IndividualAttendance", "Student", "Staff", "Teacher",
    "Admin"
]
