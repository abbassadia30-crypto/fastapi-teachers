from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginSchema(BaseModel):
    email: str
    password: str

class UserSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class StudentCreate(BaseModel):
    unique_id: Optional[str] = None
    student_name: str = Field(..., min_length=2)
    father_name: str
    father_cnic: str 
    phone: str
    grade: str
    fees: int

class StudentResponse(StudentCreate):
    id: int
    created_by: Optional[str] = None  # Added to track which admin owns the student record
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    status: str
    email: str
    name: str  # This allows the backend to send the name to the frontend