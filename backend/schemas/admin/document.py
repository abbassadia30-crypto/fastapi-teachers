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

    model_config = ConfigDict(from_attributes=True)

class VaultBase(BaseModel):
    name: str
    file_type: str  # 'scan', 'translate', 'exam'
    file_size: str
    file_url: Optional[str] = None

class VaultCreate(VaultBase):
    pass

class VaultResponse(BaseModel):
    id: int
    name: str
    subject: str
    targets: List[str]
    doc_type: str
    created_at: datetime
    # We use the institution hex ref for the response to match the model
    institution_ref: str

    model_config = ConfigDict(from_attributes=True)



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



class VoucherParticular(BaseModel):
    name: str
    amount: float

class VoucherDraft(BaseModel):
    name: str
    id: str # This is the Roll No / Staff ID from the UI
    parent: Optional[str] = None
    phone: Optional[str] = None
    heads: List[VoucherParticular]

class BulkDeployPayload(BaseModel):
    billing_period: str
    mode: str # 'student', 'staff', or 'custom'
    vouchers: List[VoucherDraft]

class VoucherResponse(BaseModel):
    id: int
    name: str
    total_amount: float
    is_paid: bool

    class Config:
        from_attributes = True