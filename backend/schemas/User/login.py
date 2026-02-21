from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import date

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None# Added to match your model
    institution_id: Optional[int] = None

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str
    action: Optional[str] = "signup" # Helps differentiate logic in verify-action route

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    fcm_token: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = "unassigned"
    user: str
    institution_id: Optional[int] = None
    identity: bool
    model_config = {"from_attributes": True}

class RoleUpdate(BaseModel):
    role: str
    email: str | None = None

class SyncStateResponse(BaseModel):
    user_role: Optional[str]
    institution_id: Optional[int]
    has_identity: bool

    class Config:
        from_attributes = True

class AuthIdCreate(BaseModel):
    full_name: str
    phone_number: str
    gender: str
    dob: date
    national_id: str
    address: str
    bio: Optional[str] = None

class AuthIdResponse(BaseModel):
    id: int
    full_name: str
    message: str = "Identity verified and synced"

    class Config:
        from_attributes = True