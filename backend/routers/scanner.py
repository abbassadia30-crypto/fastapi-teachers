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

# In backend/routers/scanner.py

@router.post("/papers/scan-only")
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

        # UPDATED FOR VERIFIED GEMINI 3 FLASH
        generate_content_config = types.GenerateContentConfig(
            # Higher thinking budget now that you are verified
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=2048,
            ),
            system_instruction="""
                You are a critical academic document parser for a Pakistani institution.
                Extract every question from the image. 
                Identify question type: 'MCQs', 'Short', or 'Long'.
                Preserve Urdu and English scripts exactly.
                Return ONLY a valid JSON object: {"questions": [{"text": "string", "type": "string"}]}
            """,
            response_mime_type="application/json"
        )

        # CHANGE: Use 'gemini-3-flash' instead of 'gemini-2.0-flash'
        response = client.models.generate_content(
            model="gemini-3-flash",
            contents=[
                types.Part.from_bytes(data=content, mime_type=file.content_type),
                "Analyze this exam paper and extract all questions."
            ],
            config=generate_content_config,
        )

        # Success! Return the data to your frontend
        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        # This will now trigger your Green/Red boxes correctly
        raise HTTPException(status_code=500, detail=f"AI Scanner Error: {str(e)}")
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