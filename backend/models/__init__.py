# backend/models/__init__.py

# 1. Get the single Base from the file we just created
from .base import Base

# 2. Load the Parent tables FIRST
from .admin.institution import Institution, School, Academy, College, User

# 3. Load the profiles
from .admin.profile import UserBio, Profile

# 4. Load the Vault/Syllabus
from .admin.document import Syllabus , DateSheet , Notice , FinanceTemplate , Transaction

# 5. Load the Management models
from .admin.dashboard import Student, Staff, Teacher