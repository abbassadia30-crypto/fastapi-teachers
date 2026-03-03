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
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

        # CORRECT CONFIGURATION FOR 2026 STANDARDS
        # This removes the 'extra_forbidden' errors and enables critical reasoning
        generate_content_config = types.GenerateContentConfig(
            # Enable thinking/reasoning through 'thinking_config'
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=1024, # Optimized for Render timeout limits
            ),
            # Set resolution correctly for small Urdu/English text
            # Options are usually 'LOW', 'MEDIUM', or 'HIGH' (if supported by tier)
            # We use a direct string as the SDK expects
            system_instruction="""
                You are a critical academic examiner for a Pakistani institution.
                Task: Extract all questions from the paper with absolute accuracy.
                Preserve Urdu script. Classify as 'MCQs', 'Short', or 'Long'.
                Return ONLY valid JSON: {"questions": [{"text": "string", "type": "string"}]}
            """,
            response_mime_type="application/json"
        )

        # Using gemini-2.0-flash as it is currently the most stable
        # for high-speed critical reading on Render
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=content, mime_type=file.content_type),
                "Critically read and extract all questions from this document."
            ],
            config=generate_content_config,
        )

        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Scanner Error: {str(e)}")
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