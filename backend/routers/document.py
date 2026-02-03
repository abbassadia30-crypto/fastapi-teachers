from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.admin.document import Syllabus, DateSheet, Notice
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.admin.institution import Institution, User
from backend.schemas.admin.document import VaultUpload, DateSheetResponse, DateSheetCreate, \
    NoticeCreate, NoticeResponse

router = APIRouter(
    prefix="/document",
    tags=["document Management"]
)

@router.post("/vault/upload")
async def upload_to_vault(
        data: VaultUpload,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    # 1. 🏛️ Get the Institution Record
    # We query by current_user.institution_id to get the hex reference
    inst = db.query(Institution).filter(
        Institution.id == current_user.institution_id
    ).first()

    if not inst:
        raise HTTPException(status_code=404, detail="Institution record not found")

    # 2. 🏛️ Set Author name safely
    author = getattr(current_user, 'name', 'Unknown Instructor')

    # 3. 🏛️ Create the Syllabus instance
    # FIX: We use 'institution_ref' to match your SQLAlchemy Class 'Syllabus'
    new_doc = Syllabus(
        institution_ref=inst.institution_id, # Mapping to the hex ref
        name=data.name,
        subject=data.subject,
        targets=data.targets,                # SQLAlchemy handles List -> JSON
        doc_type=data.doc_type,              # Usually 'syllabus'
        content=data.content,                # SQLAlchemy handles List[Dict] -> JSON
        author_name=author
    )

    try:
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # Return the VaultResponse compatible structure
        return {
            "status": "success",
            "id": new_doc.id,
            "name": new_doc.name,
            "institution_ref": new_doc.institution_ref
        }

    except Exception as e:
        db.rollback()
        # Essential for debugging the 500 error in Render logs
        print(f"CRITICAL VAULT ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database Sync Failed: {str(e)}"
        )

@router.post("/create", response_model=DateSheetResponse)
def create_datesheet(
        payload: DateSheetCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 🏛️ 1. Validation for Institution Context
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="User not linked to an institution")

    # 🏛️ 2. Creating the Instance
    # FIX: Change 'institution_id' to 'institution_ref' to match your model
    new_ds = DateSheet(
        institution_ref=current_user.institution_id, # Match the hex string ref
        title=payload.title,
        target=payload.target,
        # model_dump() is correct for Pydantic v2 to store as JSON
        exams=[e.model_dump() for e in payload.exams],
        created_by=current_user.email
    )

    try:
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)
        return new_ds
    except Exception as e:
        db.rollback()
        # Log the specific database error to Render console
        print(f"DATESHEET DB ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save DateSheet to Institution records")



@router.post("/publish", response_model=NoticeResponse)
def publish_notice(
        payload: NoticeCreate, # FastAPI automatically validates this
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution not linked")

    try:
        # Use payload.title and payload.message
        new_notice = Notice(
            institution_id=current_user.institution_id,
            title=payload.title,
            message=payload.message,
            language=payload.language,
            created_by=current_user.email
        )

        db.add(new_notice)
        db.commit()
        db.refresh(new_notice)
        return new_notice

    except Exception as e:
        db.rollback()
        # This will now print the actual error if it persists
        print(f"DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save notice")

