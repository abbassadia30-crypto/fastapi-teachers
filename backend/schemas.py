from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

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
    # We remove institution_code from "Create" schemas if you want it auto-generated

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
    section: str
    fee: float
    admitted_by: str
    institution_id: int # Needed to link student to an institute
    extra_fields: Optional[Dict[str, Any]] = None 

class StudentResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: Any
    model_config = ConfigDict(from_attributes=True)