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

# Initialize client using the Env Var you set in Render
client = genai.Client(api_key=os.environ.get("GOOGLE_AI_KEY"))

# STEP 1: The "Reader" (No DB Save)
@router.post("/papers/scan-only")
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Processing Failed: {str(e)}")

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