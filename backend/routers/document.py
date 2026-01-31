from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.admin.document import Syllabus
from backend.models.admin.institution import Institution, User

router = APIRouter(
    prefix="/document",
    tags=["document Management"]
)

@router.post("/vault/upload")
async def upload_to_vault(
        data: Syllabus,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Fetch the institution UUID based on user's institution_id
    inst = db.query(Institution).filter(Institution.id == current_user.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    new_doc = Syllabus(
        institution_ref=inst.institution_id, # Linking to the hex UUID
        name=data.name,
        doc_type=data.doc_type,
        content=data.content, # This is the nested JSON
        author_name=current_user.name
    )

    db.add(new_doc)
    db.commit()
    return {"status": "success"}