from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    institution_id: Optional[int] = None

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
    description: Optional[str] = None

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
    extra_fields: Optional[Dict[str, Any]] = None 

class StudentResponse(BaseModel):
    id: int
    name: str
    father_name: str
    section: str
    fee: float
    institution_id: int
    is_active: bool
    created_at: Any
    model_config = ConfigDict(from_attributes=True)

class Student_update(BaseModel):
    # In an update, everything should be Optional
    name: Optional[str] = None
    father_name: Optional[str] = None
    section: Optional[str] = None
    fee: Optional[float] = None
    extra_fields: Optional[Dict[str, Any]] = None 
    is_active: Optional[bool] = None

# --- Staff Schemas ---

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
    model_config = ConfigDict(from_attributes=True)

class StaffListResponse(BaseModel):
    institution_id: int
    total_employees: int
    rows: List[StaffResponse]

class PaySearchResponse(BaseModel):
    id: int
    name: str
    father_name: Optional[str] = "N/A"
    contact: Optional[str] = "N/A"
    section: Optional[str] = "N/A"
    designation: Optional[str] = None 
    work_subject: Optional[str] = None 
    
    # Financial breakdown for transparency
    base_amount: float     # The current month's fee or salary
    arrears: float         # Carried forward debt from previous months
    total_amount: float    # base_amount + arrears
    
    paid: float
    remaining: float
    status: str            # "Paid", "Partial", "Unpaid"
    
    model_config = ConfigDict(from_attributes=True)

class PaymentSubmit(BaseModel):
    id: int
    category: str          # "student" or "staff"
    amount_paid: float
    month: str             # Format: "2026-01"
    # If fee/salary was never set during admission/hiring
    actual_amount_input: Optional[float] = 0.0 

class HistoricalRecordExport(BaseModel):
    institution_name: str
    year: int
    # We use List[Dict] so we can dump the entire row for the CSV/Phone storage
    records: List[Dict[str, Any]]
