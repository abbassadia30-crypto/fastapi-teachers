from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

# Internal Imports
from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.models.admin.document import Syllabus  # Assuming consistent naming
from backend.schemas.admin.document import VaultUpload

router = APIRouter(
    prefix="/central_vault",
    tags=["Central Vault Management"]
)

# --- 1. FETCH ALL SYLLABUS DOCS ---
@router.get("/vault/list")
async def get_syllabus_list(
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    """
    Retrieves all syllabus documents specifically for the logged-in institution.
    """
    try:
        # Security: strictly filter by institution_id (the hex ref)
        docs = db.query(Syllabus).filter(
            Syllabus.institution_ref == current_user.institution_id
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
        current_user: Any = Depends(get_current_user)
):
    """
    Updates a specific document. Includes security check to prevent
    cross-institution editing.
    """
    doc = db.query(Syllabus).filter(
        Syllabus.id == doc_id,
        Syllabus.institution_ref == current_user.institution_id
    ).first()

    if not doc:
        # 404 is safer/cleaner here than 403 to avoid leaking record existence
        raise HTTPException(status_code=404, detail="Document not found in your institution")

    # Mapping updated fields
    doc.name = payload.name
    doc.subject = payload.subject
    doc.targets = payload.targets
    doc.content = payload.content

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
        payload: dict = Body(...), # Expecting format: {"ids": [1, 2, 3]}
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    """
    Deletes multiple records. Uses False for synchronize_session for
    high-performance bulk deletion.
    """
    ids_to_delete = payload.get("ids", [])

    if not ids_to_delete:
        return {"status": "success", "deleted_count": 0}

    try:
        # Security: Ensure query only captures records belonging to THIS institution
        query = db.query(Syllabus).filter(
            Syllabus.id.in_(ids_to_delete),
            Syllabus.institution_ref == current_user.institution_id
        )

        deleted_count = query.count()

        # PRO TIP: synchronize_session=False is faster for bulk operations
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