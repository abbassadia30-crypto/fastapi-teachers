import uuid
from sqlalchemy import Text

from sqlalchemy import Column, Integer, String, Boolean, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(String, unique=True, index=True, nullable=False, 
                            default=lambda: str(uuid.uuid4().hex[:8].upper()))
    type = Column(String(50)) 
    name = Column(String, nullable=False)
    address = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    owner = relationship("User", back_populates="owned_institution", foreign_keys=[owner_id])
    students = relationship("Student", back_populates="institution")
    staff_members = relationship("Staff", back_populates="institution")
    teachers = relationship("Teacher", back_populates="institution")

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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="unassigned")# Set to None/Null for onboarding later
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)
    has_institution = Column(Boolean, default=False)
    institution_id = Column(Integer, ForeignKey("institutions.id") , nullable=True)

    bio = relationship("UserBio", back_populates="user", uselist=False)
    owned_institution = relationship("Institution", back_populates="owner", 
                                     foreign_keys=[Institution.owner_id], uselist=False)
    profile = relationship("Profile", back_populates="owner", uselist=False)
    employed_at = relationship("Institution", foreign_keys=[institution_id])

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    section = Column(String, nullable=False)
    fee = Column(Float, nullable=False)
    admitted_by = Column(String, index=True) 
    extra_fields = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    institution = relationship("Institution", back_populates="students")

class Teacher(Base):
    __tablename__ = "teacher_records"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject_expertise = Column(String) # Specific to teachers
    phone = Column(String)
    salary = Column(Float)
    joining_date = Column(String)
    is_active = Column(Boolean, default=True)
    extra_details = Column(JSON, nullable=True) # For those flexible fields

    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True)
    institution = relationship("Institution", back_populates="teachers")

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    cnic = Column(String, nullable=True)
    contact = Column(String, nullable=True)

    # This is perfect as is
    extra_details = Column(JSON, nullable=True, default={})

    institution_id = Column(Integer, ForeignKey("institutions.id"))

    # RECOMMENDED ADDITION:
    # This allows you to access institution details easily: staff.institution.name
    institution = relationship("Institution", back_populates="staff_members")

class FeeRecord(Base):
    __tablename__ = "fee_records"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    arrears = Column(Float, default=0.0) 
    total_due = Column(Float) # monthly_fee + arrears
    amount_paid = Column(Float, default=0.0)
    remaining_balance = Column(Float)
    month = Column(String) # YYYY-MM
    status = Column(String) 
    is_archived = Column(Boolean, default=False)

class SalaryRecord(Base):
    __tablename__ = "salary_records"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teacher_records.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    arrears = Column(Float, default=0.0) 
    total_due = Column(Float)
    amount_paid = Column(Float, default=0.0)
    remaining_balance = Column(Float)
    month = Column(String)
    status = Column(String)
    is_archived = Column(Boolean, default=False)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    author = relationship("User")
    # Changed "Post" to "post" (lowercase) to match the attribute in Like/Comment
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    # 🏛️ Added this to resolve the Mapper error
    post = relationship("Post", back_populates="likes")
    user = relationship("User")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String(500))

    # 🏛️ Added this to resolve the Mapper error
    post = relationship("Post", back_populates="comments")
    user = relationship("User")

class UserBio(Base):
    __tablename__ = "user_bios"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    short_bio = Column(Text, nullable=True)
    custom_details = Column(JSON, nullable=True, default={})
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # This matches the 'bio' property we just added to User
    user = relationship("User", back_populates="bio")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, index=True)
    short_bio = Column(Text)
    custom_details = Column(JSON)
    owner = relationship("User", back_populates="profile")

class VaultDocument(Base):
    __tablename__ = "institution_vault"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    name = Column(String, nullable=False) # e.g., "Physics Syllabus - Grade 10"
    doc_type = Column(String) # syllabus, exam, translate, or scan
    content = Column(JSON, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    institution = relationship("Institution")