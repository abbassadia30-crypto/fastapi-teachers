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
# In backend/routers/scanner.py

@router.post("/papers/scan-only")
async def scan_only(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

        # 1. DEFINE THE CONFIG FIRST (Fixes the NameError)
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=1024, # Professional limit for Render stability
            ),
            system_instruction="""
              Extract questions from image. 
              If question is MCQ, extract its 4 options into a list named 'options'.
              Identify type: 'MCQs', 'Short', or 'Long'.
              Return ONLY JSON: {"questions": [{"text": "string", "type": "string", "options": ["A", "B", "C", "D"]}]}
            """,
            response_mime_type="application/json"
        )

        try:
            # 2. Attempt using Gemini 3
            print("Attempting scan with Gemini 3 Flash Preview...")
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Part.from_bytes(data=content, mime_type=file.content_type),
                    "Critically read and extract all questions from this document."
                ],
                config=generate_content_config, # Now defined correctly!
            )
        except Exception as e:
            # 3. Fallback logic for high demand (503)
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print("Gemini 3 Busy - Falling back to Gemini 2.5 Flash")
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=content, mime_type=file.content_type),
                        "Analyze this exam paper and extract all questions."
                    ],
                    config=generate_content_config,
                )
            else:
                raise e

        # 4. Parse and return the JSON
        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        # Triggers the RED SIGN BOX in generate_paper.html
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


@router.post("/admission/scan-register")
async def scan_admission_register(
        file: UploadFile = File(...),
        current_user: Any = Depends(get_current_user)
):
    try:
        content = await file.read()

        # 1. Define the "Soft" Configuration for maximum flexibility
        admission_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_budget=1024
            ),
            system_instruction="""
                You are an expert registrar for a Pakistani institution. 
                Task: Extract student registration details from the image.
                
                LOGIC:
                1. Identify core fields: 'name', 'father_name', 'section', and 'fee'.
                2. If you find ANY other information (e.g., 'B-Form', 'Phone', 'Address', 'DOB'), 
                   place it inside a dictionary called 'extra_fields'.
                3. Do not ignore data. If the register has a column you don't recognize, 
                   add it to 'extra_fields'.
                4. Return ONLY a valid JSON object.
                
                SCHEMA:
                {
                  "name": "string or null", 
                  "father_name": "string or null", 
                  "section": "string or null", 
                  "fee": number,
                  "extra_fields": { "Field_Name": "Value", ... }
                }
            """,
            response_mime_type="application/json"
        )

        try:
            # STEP 1: Attempt using the "Extraordinary" Model (Gemini 3)
            print("Admission Scan: Attempting Gemini 3 Flash Preview...")
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Part.from_bytes(data=content, mime_type=file.content_type),
                    "Critically read this register entry and extract all student data."
                ],
                config=admission_config,
            )
        except Exception as e:
            # STEP 2: Fallback for high stability (Gemini 2.5 Flash)
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print("Admission Scan: Gemini 3 Busy - Falling back to Gemini 2.5 Flash")
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Part.from_bytes(data=content, mime_type=file.content_type),
                        "Extract student registration info from this image."
                    ],
                    config=admission_config,
                )
            else:
                raise e

        # STEP 3: Return the "soft" JSON response
        return json.loads(response.text)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Admission Scanner Error: {str(e)}"
        )