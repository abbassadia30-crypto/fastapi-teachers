from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List

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