from xmlrpc.client import boolean
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    institution_id: int

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class RoleUpdate(BaseModel):
    email: EmailStr
    role: str # 'admin', 'teacher', etc.

# --- Institution Schemas ---
class InstitutionBase(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[EmailStr] = None

class SchoolSchema(InstitutionBase):
    principal_name: str
    campus: Optional[str] = None
    website: Optional[str] = None
    type: Literal["school"] = "school"

class AcademySchema(InstitutionBase):
    edu_type: str
    campus_name: Optional[str] = None
    contact: str
    type: Literal["academy"] = "academy"

class CollegeSchema(InstitutionBase):
    dean_name: str
    code: Optional[str] = None
    uni: Optional[str] = None
    type: Literal["college"] = "college"

# --- Student Schemas ---
class AdmissionPayload(BaseModel):
    name: str
    father_name: str
    email : EmailStr
    section: str
    fee: float
    admitted_by: str
    is_active : boolean
    institution_id: int # Needed to link student to an institute
    extra_fields: Optional[Dict[str, Any]] = None 

class StudentResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: Any
    model_config = ConfigDict(from_attributes=True)

class Student_update(AdmissionPayload):
    name: str[Optional]
    father_name: str[Optional]
    section: str[Optional]
    fee: float[Optional]
    extra_fields: Optional[Dict[str, Any]] = None 

class StaffBase(BaseModel):
    name: str
    designation: str # e.g., Teacher, Driver, Clerk
    phone: str
    salary: float
    joining_date: str # You can use 'date' type, but 'str' is easier for simple records
    
    # This field acts like the extra columns in Excel
    # You can send: {"Address": "Street 1", "Experience": "5 Years"}
    extra_details: Optional[Dict[str, Any]] = {}

# --- Schema for Creating Staff ---
class StaffCreate(StaffBase):
    pass # Uses all fields from StaffBase

# --- Schema for Updating Staff ---
class StaffUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    salary: Optional[float] = None
    extra_details: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

# --- Schema for the Response (What the API returns) ---
class StaffResponse(StaffBase):
    id: int
    institution_id: int
    is_active: bool

    class Config:
        from_attributes = True # This allows Pydantic to read SQLAlchemy models