from pydantic import ConfigDict
from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime , date
from typing import Optional, List


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
    subject: str
    paper_date: date
    paper_time: str
    duration: int
    venue: str
    day: Optional[str] = None

class DateSheetCreate(BaseModel):
    title: str
    target: str
    exams: List[ExamEntry]

class DateSheetResponse(BaseModel):
    id: int
    title: str
    target: str
    exams: List[ExamEntry]
    created_at: str

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
    created_at: str

    class Config:
        from_attributes = True

    from pydantic import BaseModel
from typing import List, Dict, Optional

class FeeHead(BaseModel):
    name: str
    amount: float

class FinanceTemplateCreate(BaseModel):
    target_group: str
    billing_month: str
    mode: str
    issue_date: str
    due_date: str
    heads: List[FeeHead]

class FinanceResponse(BaseModel):
    status: str
    template_id: int
    vouchers_generated: int
