from xmlrpc.client import boolean
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any

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
    role: str 

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

class AdmissionPayload(BaseModel):
    name: str
    father_name: str
    email : EmailStr
    section: str
    fee: float
    admitted_by: str
    is_active : boolean
    institution_id: int 
    extra_fields: Optional[Dict[str, Any]] = None 

class StudentResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: Any
    model_config = ConfigDict(from_attributes=True)

class Student_update(AdmissionPayload):
    name: Optional[str]
    father_name: Optional[str]
    section: Optional[str]
    fee: Optional[float]
    extra_fields: Optional[Dict[str, Any]] = None 

class StaffBase(BaseModel):
    name: str
    designation: str 
    phone: str
    salary: float
    joining_date: str 
    extra_details: Optional[Dict[str, Any]] = {}

class StaffCreate(StaffBase):
    pass 

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    salary: Optional[float] = None
    extra_details: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class StaffResponse(StaffBase):
    id: int
    institution_id: int
    is_active: bool

    class Config:
        from_attributes = True 