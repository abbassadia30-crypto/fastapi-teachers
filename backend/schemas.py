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
    Roll_number : int
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

class StudentBase(BaseModel):
    student_name: str
    father_name: str
    grade: str
    phone: str
    fees: int
    father_cnic: Optional[str] = None
    created_by: str

class StudentCreate(StudentBase):
    pass

# This is the critical part for the Frontend
class StudentResponse(StudentBase):
    id: int  # The database ID must be here

    class Config:
        from_attributes = True

class UpdateStudent(BaseModel):
    student_name: Optional[str] = None
    father_name: Optional[str] = None
    grade: Optional[str] = None
    phone: Optional[str] = None
    fees: Optional[int] = None
    father_cnic: Optional[str] = None

class EmailSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    email: str
    otp: str
    new_password: str    