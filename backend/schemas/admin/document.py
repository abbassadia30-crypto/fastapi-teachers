from pydantic import ConfigDict, Field
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from backend.models.admin.document import VoucherMode


class VaultUpload(BaseModel):
    name: str
    doc_type: str
    content: List[Dict[str, Any]] # Stores the nested Books/Chapters
    model_config = ConfigDict(from_attributes=True)

class VaultBase(BaseModel):
    name: str
    file_type: str  # 'scan', 'translate', 'exam'
    file_size: str
    file_url: Optional[str] = None

class VaultCreate(VaultBase):
    pass

class VaultResponse(VaultBase):
    id: int
    created_at: datetime
    institution_id: int

    class Config:
        from_attributes = True

class ExamEntry(BaseModel):
    subject_name: str
    date: str
    time: str
    duration_mins: int
    venue: str

class DateSheetCreate(BaseModel):
    title: str
    target: str
    exams: List[ExamEntry]

class DateSheetResponse(BaseModel):
    id: int
    title: str
    target: str
    exams: List[ExamEntry]
    created_at: datetime  # <--- Change 'str' to 'datetime'

    class Config:
        from_attributes = True

class NoticeCreate(BaseModel):
    title: str
    message: str
    language: str = "en"

class NoticeResponse(BaseModel):
    id: int
    title: str
    message: str
    language: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HeadCreate(BaseModel):
    name: str = Field(..., example="Tuition Fee")
    amount: float = Field(..., gt=0, example=5000.0)

class FinanceTemplateCreate(BaseModel):
    target_group: str = Field(..., example="Grade 10-A")
    billing_month: str = Field(..., example="2026-02")
    mode: VoucherMode  # Uses the Enum: 'student' or 'staff'
    issue_date: str    # Format: YYYY-MM-DD
    due_date: str      # Format: YYYY-MM-DD
    heads: List[HeadCreate]

    class Config:
        from_attributes = True