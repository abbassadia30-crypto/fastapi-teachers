# 1. Get the single Base
from backend.models.base import Base

# 2. Load the Parent tables (Institution & User) FIRST
from backend.models.admin.institution import Institution, School, Academy, College, User

# 3. Load the profiles (Dependent on User)
from backend.models.admin.profile import UserBio, Profile

# 4. Load the Vault/Syllabus (Dependent on Institution)
from backend.models.admin.document import Syllabus

# 5. Load the Management models (Dependent on Institution)
from backend.models.admin.dashboard import Student, Staff, Teacher