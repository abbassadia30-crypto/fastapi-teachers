from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: optional[str] = None# Added to match your model
    institution_id: Optional[int] = None

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str
    action: Optional[str] = "signup" # Helps differentiate logic in verify-action route

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

class Joining(BaseModel):
    request_message = str
    sent_by = int
    sent_to = int

class Approval(BaseModel):
    request_id = int
    Approval = boolean