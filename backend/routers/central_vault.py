from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any
from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.models.admin.document import Syllabus
from backend.schemas.admin.document import VaultUpload
# CORRECTED: Import the new response model
from backend.schemas.admin.central_vault import SyllabusResponse

router = APIRouter(
    prefix="/central_vault",
    tags=["Central Vault Management"]
)

# --- 1. FETCH ALL SYLLABUS DOCS ---
# CORRECTED: Use the response_model to ensure proper serialization
@router.get("/vault/list", response_model=List[SyllabusResponse])
async def get_syllabus_list(
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user) # Changed dict to Any or your User model
):
    try:
        # FIX: Use dot notation .institution_id instead of ["institution_id"]
        # Also ensure your get_current_user is actually returning the owner/admin object
        institution_id = getattr(current_user, "institution_id", None)

        if not institution_id:
            raise HTTPException(status_code=401, detail="Institution reference not found")

        docs = db.query(Syllabus).filter(
            Syllabus.institution_ref == institution_id
        ).order_by(Syllabus.created_at.desc()).all()

        return docs
    except Exception as e:
        print(f"VAULT FETCH ERROR: {str(e)}")
        # It's better to log the error specifically for debugging
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# --- 2. UPDATE SYLLABUS ---
@router.put("/vault/update/{doc_id}")
async def update_syllabus(
        doc_id: int,
        payload: VaultUpload,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    inst_id = getattr(current_user, "institution_id", None)

    doc = db.query(Syllabus).filter(
        Syllabus.id == doc_id,
        Syllabus.institution_ref == inst_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # FIX: Remove the list comprehension and model_dump()
    # If payload.content is already a list of dicts, just assign it.
    try:
        if hasattr(payload.content[0], "model_dump"):
            doc.content = [item.model_dump() for item in payload.content]
        else:
            doc.content = payload.content

        doc.name = payload.name
        doc.subject = payload.subject
        doc.targets = payload.targets

        db.commit()
        return {"status": "success", "message": "Updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"UPDATE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update content")

@router.post("/vault/delete-bulk")
async def delete_syllabus_bulk(
        payload: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    ids_to_delete = payload.get("ids", [])
    inst_id = getattr(current_user, "institution_id", None)

    if not ids_to_delete:
        return {"status": "success", "deleted_count": 0}

    try:
        # FIX: Use dot notation .institution_id
        query = db.query(Syllabus).filter(
            Syllabus.id.in_(ids_to_delete),
            Syllabus.institution_ref == inst_id
        )

        deleted_count = query.count()
        query.delete(synchronize_session=False)
        db.commit()

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} items"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")

@router.get("/papers/history-list")
async def get_history_papers(
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    inst_id = getattr(current_user, 'institution_id', None)
    if not inst_id:
        raise HTTPException(status_code=403, detail="Not linked to institution")

    # Fetching papers that have already been exported/printed
    papers = db.query(PaperVault).filter(
        PaperVault.institution_ref == inst_id,
        PaperVault.status == "taken"
    ).all()

    return papers