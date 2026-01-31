from pydantic import BaseModel
from typing import Optional, Dict

class ProfileUpdate(BaseModel):
    full_name: str
    short_bio: Optional[str] = None
    custom_details: Optional[Dict[str, str]] = None

# 🏛️ What the Backend sends to the Explore Page
class ProfileOut(BaseModel):
    full_name: str
    short_bio: Optional[str]
    custom_details: Optional[Dict[str, str]]

    class Config:
        from_attributes = True
