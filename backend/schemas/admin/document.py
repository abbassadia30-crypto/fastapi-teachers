from pydantic import ConfigDict
from typing import Dict, Any
from datetime import datetime , date
from pydantic import BaseModel
from typing import Optional, List

from backend.models.admin.document import VoucherMode


class VaultUpload(BaseModel):
    id: Optional[int] = None      # Add this to handle resumed IDs
    name: str
    subject: str
    targets: List[str]
    doc_type: str = "syllabus"
    content: List[Any]
    is_final: Optional[bool] = True

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

class ResultEntry(BaseModel):
    student_id: int  # Must be int
    name: str
    father_name: str
    marks: List[MarkEntry]

class BulkResultPayload(BaseModel):
    exam_title: str
    class_name: str
    is_draft: bool
    results: List[ResultEntry]

class QuestionEntry(BaseModel):
    text: str
    sub_parts: List[str] = []

class BlueprintSection(BaseModel):
    type: str
    marks_per_q: int
    choice: int
    questions: List[QuestionEntry] # Change from List[str] to List[QuestionEntry]

class QuestionModel(BaseModel):
    text: str
    sub_parts: List[str] = []

# 2. Define the middle unit (The Section)
class SectionModel(BaseModel):
    type: str
    marks_per_q: int
    choice: int
    questions: List[QuestionModel]

# 3. Define the main payload (The Paper)
class PaperCreate(BaseModel):
    institution: str
    subject: str
    target_class: str
    paper_type: str
    duration: str
    language: str
    blueprint: List[SectionModel]  # Now Python knows what SectionModel is!
    total_marks: int

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

class PendingSync(BaseModel):
    id: Optional[int] = None  # Crucial for resuming
    name: str
    subject: str
    targets: List[str]
    content: List[Any]
    doc_type: str = "syllabus_draft"


class ScannedQuestion(BaseModel):
    text: str
    type: str # MCQs, Short, Long
    marks: Optional[int] = 1

class ScannedBankCreate(BaseModel):
    source_name: Optional[str] = "Untitled Scan"
    questions: List[ScannedQuestion]

class ScannedBankResponse(BaseModel):
    id: int
    source_name: str
    questions_data: List[ScannedQuestion]
    created_at: datetime

    class Config:
        from_attributes = True