from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Added for the Verify.html page logic
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class StudentCreate(BaseModel):
    unique_id: Optional[str] = None
    student_name: str
    father_name: str
    father_cnic: Optional[str] = None
    phone: str
    grade: str
    fees: int

class StudentResponse(StudentCreate):
    id: int
    created_by: str
    
    class Config:
        from_attributes = True