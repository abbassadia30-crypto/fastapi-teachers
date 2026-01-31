from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List

class PaySearchResponse(BaseModel):
    id: int
    name: str
    father_name: Optional[str] = "N/A"
    contact: Optional[str] = "N/A"
    section: Optional[str] = "N/A"
    designation: Optional[str] = None 
    work_subject: Optional[str] = None 
    
    # Financial breakdown for transparency
    base_amount: float     # The current month's fee or salary
    arrears: float         # Carried forward debt from previous months
    total_amount: float    # base_amount + arrears
    
    paid: float
    remaining: float
    status: str            # "Paid", "Partial", "Unpaid"
    
    model_config = ConfigDict(from_attributes=True)

class PaymentSubmit(BaseModel):
    id: int
    category: str          # "student" or "staff"
    amount_paid: float
    month: str             # Format: "2026-01"
    # If fee/salary was never set during admission/hiring
    actual_amount_input: Optional[float] = 0.0 

class HistoricalRecordExport(BaseModel):
    institution_name: str
    year: int
    # We use List[Dict] so we can dump the entire row for the CSV/Phone storage
    records: List[Dict[str, Any]]


