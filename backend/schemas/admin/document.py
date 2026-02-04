from pydantic import ConfigDict
from typing import Dict, Any
from datetime import datetime , date
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


class SubjectResult(BaseModel):
    subject: str
    max: float
    obt: float
    pass_mark: float

class StudentMarkEntry(BaseModel):
    student_id: Optional[int] = None  # None for manual entries
    name: str
    father_name: str
    marks: List[SubjectResult]
    status: str  # "PASS" or "FAIL"

class BulkResultPayload(BaseModel):
    exam_title: str
    class_name: str
    results: List[StudentMarkEntry]



class QuestionBlock(BaseModel):
    block_type: str # 'MCQs', 'Short', 'Long', 'Custom'
    header_text: str
    marks_per_q: int
    qty: int
    questions: List[str] # The text typed in the .q-input fields

class PaperCreate(BaseModel):
    subject: str
    target_class: str
    paper_type: str
    duration: str
    language: str
    blueprint: List[QuestionBlock]
    total_marks: int

class PaperResponse(BaseModel):
    id: int
    subject: str
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True



class AttendanceEntry(BaseModel):
    student_id: str
    student_name: str
    status: str
    is_manual: bool

class AttendanceSubmit(BaseModel):
    section_id: str  # 'MANUAL' or a specific ID
    custom_section_name: Optional[str] = None
    date: date
    type: str  # 'class' or 'test'
    subject: Optional[str] = None
    data: List[AttendanceEntry]



class StaffAttendanceEntry(BaseModel):
    staff_id: str
    staff_name: str
    status: str      # P, A, or L
    role: str        # Class Teacher, Invigilator, or N/A
    is_manual: bool = False

class StaffAttendanceSubmit(BaseModel):
    category: str    # 'teacher' or 'admin-staff'
    date: date
    shift: Optional[str] = "Morning"
    data: List[StaffAttendanceEntry]