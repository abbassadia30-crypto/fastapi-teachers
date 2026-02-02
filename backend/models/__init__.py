# backend/models/__init__.py

# 1. Get the single Base
from .base import Base
# 2. Import models (ensure each class is imported only ONCE)
from .admin.institution import Institution, School, Academy, College
from .admin.institution import User # Import User from its actual source
from .admin.profile import UserBio, Profile
from .admin.document import Syllabus, DateSheet, Notice, Transaction, FinanceTemplate
from .admin.dashboard import Student, Staff, Teacher

# Ensure all are available for main.py
__all__ = [
    "Base", "User", "Institution", "Syllabus",
    "School", "Academy", "College", "UserBio",
    "Profile", "DateSheet", "Notice", "Transaction",
    "FinanceTemplate", "Student", "Staff", "Teacher"
]