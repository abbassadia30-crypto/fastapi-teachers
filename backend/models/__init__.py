# backend/models/__init__.py

from .base import Base

# 1. Import the "Leaf" models first (things that don't depend on Institution as much)
from .admin.document import Syllabus, DateSheet, Notice, Voucher , AcademicResult , PaperVault , AttendanceLog , IndividualAttendance
from .admin.profile import UserBio, Profile

# 2. Import the "Core" models
# Make sure User is imported from its correct location
from .admin.institution import User  # Check if this path is actually /admin/institution.py or /users.py

# 3. Import Institution last
from .admin.institution import Institution, School, Academy, College
from .admin.dashboard import Student, Staff, Teacher

__all__ = [
    "Base", "User", "Institution", "Syllabus",
    "School", "Academy", "College", "UserBio",
    "Profile", "DateSheet", "Notice", "Voucher" , "AcademicResult" , "PaperVault" , "IndividualAttendance" , "AttendanceLog" ,
    "Student", "Staff", "Teacher"
]