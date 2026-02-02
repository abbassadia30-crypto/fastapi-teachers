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
    # Log the ID to debug if the user session is correct
    print(f"Uploading for User ID: {current_user.id}, Inst ID: {current_user.institution_id}")

    inst = db.query(Institution).filter(
    Institution.id == current_user.institution_id
    ).first()

    if not inst:
       raise HTTPException(status_code=404, detail="Institution record not found")


    # Use getattr to safely get the name if it's missing
    author = getattr(current_user, 'name', 'Unknown Instructor')

    new_doc = Syllabus(
    institution_id =inst.institution_id,  # STRING UUID
    name=data.name,
    subject=data.subject,
    targets=data.targets,
    doc_type=data.doc_type,
    content=data.content,
    author_name=author
)


    try:
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        return {"status": "success", "id": new_doc.id}
    except Exception as e:
        db.rollback()
        # This will show the exact SQL error in your Render logs
        print(f"DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vault Sync Failed: {str(e)}")

@router.post("/create", response_model=DateSheetResponse)
def create_datesheet(
        payload: DateSheetCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="Institution not found")

    new_ds = DateSheet(
        institution_id=current_user.institution_id,
        title=payload.title,
        target=payload.target,
        exams=[e.model_dump() for e in payload.exams],
        created_by=current_user.email
    )

    db.add(new_ds)
    db.commit()
    db.refresh(new_ds)
    return new_ds


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

