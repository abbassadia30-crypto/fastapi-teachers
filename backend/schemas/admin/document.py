from pydantic import ConfigDict
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from backend.models.admin.document import VoucherMode


class VaultUpload(BaseModel):
    name: str
    subject: str
    targets: List[str]
    doc_type: str
    content: List[Dict[str, Any]]

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
    name: str
    amount: float

class VoucherBulkCreate(BaseModel):
    target_group: str
    billing_month: str
    mode: VoucherMode
    issue_date: str
    due_date: str
    heads: List[HeadCreate]

class FinanceTemplateCreate(BaseModel):
    target_group: str
    billing_month: str
    mode: VoucherMode
    issue_date: str
    due_date: str
    heads: List[HeadCreate]