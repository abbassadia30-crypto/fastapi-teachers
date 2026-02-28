from fastapi import APIRouter, UploadFile, File, HTTPException
from google.cloud import documentai
import os
import re
from backend.models.admin.document import PaperVault # Assuming this exists
from backend.routers.auth import get_current_user
from backend.database import get_db

router = APIRouter(
    prefix="/scanner",
    tags=["Paper Management"]
)


@router.post("/papers/scan-and-save")
async def scan_and_save(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    # 1. Google Document AI Processing
    client = documentai.DocumentProcessorServiceClient()
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    content = await file.read()
    raw_document = documentai.RawDocument(content=content, mime_type=file.content_type)

    result = client.process_document(request=documentai.ProcessRequest(name=name, raw_document=raw_document))

    # 2. Professional Parser Logic (Regex for Q numbers, Marks, etc.)
    full_text = result.document.text
    # Split by common question patterns like "Q1.", "1.", "Part-I"
    raw_sections = re.split(r'\n(?=\d+\.|Q\d+[:\s])', full_text)

    parsed_qs = []
    for s in raw_sections:
        if len(s.strip()) < 15: continue
        q_type = "MCQs" if "(a)" in s or "(b)" in s else "Short"
        if len(s) > 200: q_type = "Long"
        parsed_qs.append({"text": s.strip(), "type": q_type})

    # 3. Save to DB linked to user_email
    new_entry = PaperVault(
        institution_ref=current_user.institution_id,
        creator_email=current_user.user_email,
        title=f"Scanned_{datetime.now().strftime('%Y%m%d_%H%M')}",
        content={"questions": parsed_qs}, # Storing as JSON
        category="AI_SCANNED"
    )
    db.add(new_entry)
    db.commit()

    return {"status": "success", "questions": parsed_qs}