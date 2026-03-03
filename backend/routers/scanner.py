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
from google.genai.types import HttpOptions

router = APIRouter(prefix="/scanner", tags=["Scanner Management"])

# Initialize client - Gemini 3 Flash is accessed via the latest SDK
client = genai.Client(
    api_key=os.environ.get("GOOGLE_AI_KEY"),
    http_options=HttpOptions(api_version="v1beta")
)

# In backend/routers/scanner.py
@router.post("/papers/scan-only")
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

        # System instructions for consistent extraction
        system_prompt = """
            Extract every question from the image. 
            Identify question type: 'MCQs', 'Short', or 'Long'.
            Preserve Urdu and English scripts exactly.
            Return ONLY a valid JSON object: {"questions": [{"text": "string", "type": "string"}]}
        """

        try:
            # STEP 1: Attempt using the "Extraordinary" Model (Gemini 3)
            print("Attempting scan with Gemini 3 Flash Preview...")
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Part.from_bytes(data=content, mime_type=file.content_type),
                    system_prompt
                ],
                config=generate_content_config,
            )
        except Exception as e:
            # STEP 2: Fallback if Gemini 3 is busy (503) or unavailable
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print("Gemini 3 Busy - Falling back to Gemini 2.5 Flash (Stable)")
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=content, mime_type=file.content_type),
                        system_prompt
                    ],
                    config=generate_content_config,
                )
            else:
                # If it's a different error (like a 401 or 400), we don't want to hide it
                raise e

        # STEP 3: Parse and return the response
        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        # This triggers your Red Box in the frontend
        raise HTTPException(
            status_code=500,
            detail=f"Institution Scanner Error: {str(e)}"
        )

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