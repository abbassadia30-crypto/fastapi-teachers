import os
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from typing import Any

# Internal Imports
from .auth import get_current_user
from backend.database import get_db
from backend.models.admin.document import ScannedQuestionBank
from backend.schemas.admin.document import ScannedBankResponse, ScannedBankCreate

router = APIRouter(prefix="/scanner", tags=["Scanner Management"])

# Initialize client - Gemini 3 Flash is accessed via the latest SDK
client = genai.Client(api_key=os.environ.get("GOOGLE_AI_KEY"))

@router.post("/papers/scan-only")
async def scan_only(file: UploadFile = File(...), current_user: Any = Depends(get_current_user)):
    content = await file.read()

    # GEMINI 3 CRITICAL CONFIGURATION
    config = types.GenerateContentConfig(
        # 'MEDIUM' thinking ensures it reasons through Urdu script/Math formulas
        thinking_level="MEDIUM",
        # 'HIGH' resolution is mandatory for clear text extraction from photos
        media_resolution="HIGH",
        system_instruction="""
            You are a professional examiner for a Pakistani institution.
            Critically read the provided image/PDF. 
            Extract questions and categorize them: 'MCQs', 'Short', or 'Long'.
            Maintain exact Urdu/English script. Output ONLY valid JSON.
        """,
        response_mime_type="application/json"
    )

    # HIT THE CONNECTION
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_bytes(data=content, mime_type=file.content_type),
            "Perform a critical scan of this paper."
        ],
        config=config,
    )

    return json.loads(response.text)
# STEP 2: The "Vault" (Permanent DB Save)
@router.post("/papers/save-scanned", response_model=ScannedBankResponse)
async def save_scanned_to_vault(
        payload: ScannedBankCreate,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    try:
        # payload.questions is a list of Pydantic objects, 
        # we convert them to dicts to store in the JSONB column
        formatted_questions = [q.model_dump() for q in payload.questions]

        new_entry = ScannedQuestionBank(
            institution_id=current_user.institution_id,
            creator_email=current_user.user_email,
            source_name=payload.source_name,
            questions_data=formatted_questions,
            created_at=datetime.utcnow()
        )

        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Save Failed: {str(e)}")