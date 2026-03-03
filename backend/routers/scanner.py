from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from google import genai
from google.genai import types
import json
from sqlalchemy.orm import Session
from .auth import get_current_user
from backend.database import get_db
from typing import Any
from backend.models.admin.document import ScannedQuestionBank
from baceknd.schemas.admin.document import ScannedBankResponse


router = APIRouter(prefix="/scanner", tags=["Profile"])

# STEP 1: The "Reader" (No DB Save)
@router.post("/papers/scan-only")
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    content = await file.read()

    # Precise instruction for exam papers
    system_instruction = """
    Extract all academic questions from the image. 
    Classify each as: 'MCQs', 'Short', or 'Long'.
    Ignore headers, footers, and page numbers.
    Return ONLY JSON: {"questions": [{"text": "string", "type": "string"}]}
    """

    response = client.models.generate_content(
        model="gemini-3-flash",
        contents=[
            types.Part.from_bytes(data=content, mime_type=file.content_type),
            "Extract questions."
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json"
        )
    )

    return json.loads(response.text)

# STEP 2: The "Vault" (Permanent DB Save)
@router.post("/papers/save-scanned", response_model=ScannedBankResponse)
async def save_scanned_to_vault(
        payload: ScannedBankCreate, # Uses your Pydantic model
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    new_entry = ScannedQuestionBank(
        institution_id=current_user.institution_id,
        creator_email=current_user.user_email,
        source_name=payload.source_name,
        # Mapping 'questions' from Pydantic to 'questions_data' in DB
        questions_data=[q.dict() for q in payload.questions]
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry