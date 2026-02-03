from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.admin.document import Syllabus, DateSheet, Notice, Voucher
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.admin.institution import Institution, User
from backend.schemas.admin.document import VaultUpload, DateSheetResponse, DateSheetCreate, \
    NoticeCreate, NoticeResponse, BulkDeployPayload

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
        payload: NoticeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. 🏛️ Institutional Check
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution not linked")

    try:
        # 2. 🏛️ Map to Database Model
        # FIX: Change 'institution_id' to 'institution_ref' to match Notice model
        new_notice = Notice(
            institution_ref=current_user.institution_id, # Match SQLAlchemy column name
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
        # Essential for Render monitoring
        print(f"DATABASE ERROR (Notice): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save notice: {str(e)}")

@router.post("/finance/deploy-bulk")
async def deploy_vouchers(
        payload: BulkDeployPayload,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution context missing")

    vouchers_to_save = []

    try:
        for draft in payload.vouchers:
            # 🏛️ Calculate total on the server for security
            total = sum(item.amount for item in draft.heads)

            new_v = Voucher(
                institution_ref=current_user.institution_id,
                recipient_type=payload.mode,
                name=draft.name,
                registration_id=draft.id,
                father_name=draft.parent,
                phone=draft.phone,
                billing_period=payload.billing_period,
                particulars=[h.model_dump() for h in draft.heads],
                total_amount=total,
                created_by=current_user.email
            )
            vouchers_to_save.append(new_v)

        # 🏛️ Bulk insert for performance
        db.add_all(vouchers_to_save)
        db.commit()

        return {
            "status": "success",
            "count": len(vouchers_to_save),
            "message": f"Successfully deployed {len(vouchers_to_save)} vouchers"
        }

    except Exception as e:
        db.rollback()
        print(f"FINANCE DEPLOY ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Database integrity failure during bulk deploy")
