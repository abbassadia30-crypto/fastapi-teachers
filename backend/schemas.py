from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict  # <--- MUST HAVE CAPITAL 'D' Dict HERE

# Match the name used in your main.py
class VerifyOTP(BaseModel):
    email: str
    otp: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class AdmissionPayload(BaseModel):
    name: str
    section: str
    fee: float
    admitted_by: str
    extra_fields: str
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    email: str
    is_verified: bool
    role: Optional[str] = None 

    class Config:
        from_attributes = True

class ResetPasswordSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str