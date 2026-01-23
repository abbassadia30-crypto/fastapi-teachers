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
    # Added relationship for staff
    staff_members = relationship("Staff", back_populates="institution")

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
    role = Column(String, default="student") # Set to None/Null for onboarding later
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime(timezone=True), nullable=True)
    has_institution = Column(Boolean, default=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    
    # Ownership (For Admins)
    owned_institution = relationship("Institution", back_populates="owner", 
                                     foreign_keys=[Institution.owner_id], uselist=False)
    # Employment/Enrollment (Where they belong)
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

class Staff(Base):
    __tablename__ = "staff_records"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    designation = Column(String) 
    phone = Column(String)
    salary = Column(Float)
    joining_date = Column(String) # Format: YYYY-MM-DD
    is_active = Column(Boolean, default=True)
    extra_details = Column(JSON, nullable=True)
    
    institution_id = Column(Integer, ForeignKey("institutions.id"), index=True)
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
    staff_id = Column(Integer, ForeignKey("staff_records.id"))
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