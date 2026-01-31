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
    role: str
    email: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user: str
    institution_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)