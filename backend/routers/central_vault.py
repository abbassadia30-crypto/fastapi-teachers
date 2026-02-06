from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

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
        current_user: dict = Depends(get_current_user)
):
    """
    Retrieves all syllabus documents specifically for the logged-in institution.
    """
    try:
        # The query remains the same.
        docs = db.query(Syllabus).filter(
            Syllabus.institution_ref == current_user["institution_id"]
        ).order_by(Syllabus.created_at.desc()).all()

        return docs
    except Exception as e:
        print(f"VAULT FETCH ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve vault records")

# --- 2. UPDATE SYLLABUS ---
@router.put("/vault/update/{doc_id}")
async def update_syllabus(
        doc_id: int,
        payload: VaultUpload,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Updates a specific document. Includes security check to prevent
    cross-institution editing.
    """
    doc = db.query(Syllabus).filter(
        Syllabus.id == doc_id,
        Syllabus.institution_ref == current_user["institution_id"]
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in your institution")

    # Convert Pydantic models to dictionaries for the JSON field
    doc.content = [item.model_dump() for item in payload.content]
    # Update other fields
    doc.name = payload.name
    doc.subject = payload.subject
    doc.targets = payload.targets

    try:
        db.commit()
        return {
            "status": "success",
            "message": f"Syllabus '{payload.name}' updated successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"VAULT UPDATE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Database sync failed during update")

# --- 3. BULK DELETE ---
@router.post("/vault/delete-bulk")
async def delete_syllabus_bulk(
        payload: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Deletes multiple records.
    """
    ids_to_delete = payload.get("ids", [])

    if not ids_to_delete:
        return {"status": "success", "deleted_count": 0}

    try:
        query = db.query(Syllabus).filter(
            Syllabus.id.in_(ids_to_delete),
            Syllabus.institution_ref == current_user["institution_id"]
        )

        deleted_count = query.count()
        query.delete(synchronize_session=False)
        db.commit()

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "message": f"Purged {deleted_count} records from vault"
        }

    except Exception as e:
        db.rollback()
        print(f"BULK DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk delete operation failed")
