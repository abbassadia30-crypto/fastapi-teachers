from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List
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

class EmployeeBase(BaseModel):
    name: str
    phone: str
    salary: float = Field(..., gt=0)
    joining_date: str
    extra_details: Optional[Dict[str, Any]] = {}
    is_active: bool = True

class TeacherCreate(EmployeeBase):
    designation: str = "Teacher"
    subject_expertise: Optional[str] = None # New advanced field

class TeacherResponse(TeacherCreate):
    id: int
    institution_id: int
    model_config = ConfigDict(from_attributes=True)

class TeacherListResponse(BaseModel):
    institution_id: int
    total_teachers: int
    rows: List[TeacherResponse]

class StaffBase(BaseModel):
    name: str
    position: str
    cnic: Optional[str] = None
    contact: Optional[str] = None
    extra_details: Optional[Dict[str, str]] = {}

class StaffCreate(StaffBase):
    pass

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    cnic: Optional[str] = None
    contact: Optional[str] = None
    extra_details: Optional[Dict[str, str]] = None

class StaffResponse(StaffBase):
    id: int
    institution_id: int

    # Pydantic v2 standard for from_orm
    model_config = ConfigDict(from_attributes=True)

class StaffListResponse(BaseModel):
    institution_id: int
    total_staff: int
    rows: List[StaffResponse]

    # Adding this prevents validation errors when passing SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    salary: Optional[float] = None
    is_active: Optional[bool] = None
    extra_details: Optional[Dict[str, Any]] = None