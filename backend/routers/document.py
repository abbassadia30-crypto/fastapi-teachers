import uuid
from datetime import datetime

from fastapi import  status
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.admin.document import Syllabus, DateSheet, Notice, FinanceTemplate, Transaction
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.admin.institution import Institution, User
from backend.schemas.admin.document import VaultUpload, DateSheetResponse, DateSheetCreate, \
    NoticeCreate, NoticeResponse, VoucherBulkCreate, FinanceTemplateCreate

router = APIRouter(
    prefix="/document",
    tags=["document Management"]
)

@router.post("/vault/upload")
async def upload_to_vault(
        data: VaultUpload,  # 🌟 CHANGED THIS from Syllabus to VaultUpload
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Fetch the institution UUID based on user's institution_id
    inst = db.query(Institution).filter(Institution.id == current_user.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution staff record not found")

    # Here we use the Model class to create the DB entry
    # Using 'Syllabus' (Model) to create, while 'data' is 'VaultUpload' (Schema)
    new_doc = Syllabus(
        institution_ref=inst.institution_id,
        name=data.name,
        doc_type=data.doc_type,
        content=data.content,
        author_name=current_user.name
    )

    db.add(new_doc)
    db.commit()
    return {"status": "success"}
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
            institution_ref=current_user.institution_id,
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

@router.get("/my", response_model=list[NoticeResponse])
def list_notices(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return db.query(Notice).filter(
        Notice.institution_id == current_user.institution_id,
        Notice.is_active == True
    ).order_by(Notice.created_at.desc()).all()

@router.post("/process-bulk")
async def process_bulk_finance(
        payload: FinanceTemplateCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        # 1. Calculate Total and Save the Master Template
        total_payable = sum(h.amount for h in payload.heads)

        new_template = FinanceTemplate(
            institution_id=current_user.institution_id,
            target_group=payload.target_group,
            billing_month=payload.billing_month,
            mode=payload.mode,
            structure=[h.dict() for h in payload.heads], # Storing as JSON
            total_amount=total_payable,
            issue_date=payload.issue_date,
            due_date=payload.due_date
        )

        db.add(new_template)
        db.flush()  # Extract template ID for the transactions

        # 2. Identify Recipients
        # Real App Logic: Filtering by institution, role, and the specific group (Class/Section)
        query = db.query(User).filter(
            User.institution_id == current_user.institution_id,
            User.role == payload.mode
        )

        # If target_group is specified (e.g., 'Grade 10-A'), filter by it
        # Assuming your User model has a 'target_group' or 'section' column
        if payload.target_group and payload.target_group != "All":
            query = query.filter(User.target_group == payload.target_group)

        recipients = query.all()

        if not recipients:
            db.rollback()
            raise HTTPException(status_code=404, detail="No users found in the selected target group.")

        # 3. Mass Generate Individual Transactions (Vouchers)
        vouchers_to_create = []
        for person in recipients:
            # Generate a unique, professional voucher number
            unique_ref = f"INV-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"

            voucher = Transaction(
                institution_id=current_user.institution_id,
                user_id=person.id,
                template_id=new_template.id,
                amount=total_payable,
                status="unpaid",
                voucher_no=unique_ref
            )
            vouchers_to_create.append(voucher)

        # Bulk insert for high performance
        db.add_all(vouchers_to_create)
        db.commit()

        return {
            "status": "success",
            "template_id": new_template.id,
            "vouchers_generated": len(vouchers_to_create)
        }

    except Exception as e:
        db.rollback()
        print(f"Finance Error: {str(e)}") # Log for the developer
        raise HTTPException(status_code=500, detail="Failed to process bulk vouchers.")

