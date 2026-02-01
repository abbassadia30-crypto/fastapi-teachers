import uuid
from datetime import datetime

from fastapi import  status
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.admin.document import Syllabus, DateSheet, Notice, FinanceTemplate, Transaction, Voucher, \
    VoucherHead
from backend.routers.auth import get_current_user
from backend.database import get_db
from backend.models.admin.institution import Institution, User
from backend.schemas.admin.document import VaultUpload, DateSheetResponse, DateSheetCreate, \
    NoticeCreate, NoticeResponse, FinanceTemplateCreate, VoucherBulkCreate

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
        data: FinanceTemplateCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Save the Template
    total = sum(item.amount for item in data.heads)
    new_temp = FinanceTemplate(
        institution_id=current_user.institution_id,
        target_group=data.target_group,
        billing_month=data.billing_month,
        mode=data.mode,
        structure=[h.dict() for h in data.heads],
        total_amount=total,
        issue_date=data.issue_date,
        due_date=data.due_date
    )
    db.add(new_temp)
    db.flush() # Get the ID before committing

    # 2. Find all students in this group (Filtering by Section)
    # Note: In a real app, 'target_group' would match a 'Section' column in your Student model
    recipients = db.query(User).filter(
        User.institution_id == current_user.institution_id,
        User.role == data.mode # "student" or "staff"
    ).all()

    # 3. Generate Individual Vouchers
    for person in recipients:
        voucher = Transaction(
            institution_id=current_user.institution_id,
            user_id=person.id,
            template_id=new_temp.id,
            amount=total,
            voucher_no=f"V-{uuid.uuid4().hex[:6].upper()}"
        )
        db.add(voucher)

    db.commit()
    return {"status": "success", "vouchers_generated": len(recipients)}

@router.post("/process-bulk")
async def process_bulk_vouchers(
        payload: VoucherBulkCreate,
        db: Session = Depends(get_db),
        current_user = Depends(get_current_user)
):
    try:
        # Calculate total
        total_payable = sum(h.amount for h in payload.heads)

        # 1. Create the Main Voucher
        new_voucher = Voucher(
            institution_id=current_user.institution_id,
            target_group=payload.target_group,
            billing_month=payload.billing_month,
            mode=payload.mode,
            issue_date=datetime.strptime(payload.issue_date, '%Y-%m-%d').date(),
            due_date=datetime.strptime(payload.due_date, '%Y-%m-%d').date(),
            total_amount=total_payable
        )

        db.add(new_voucher)
        db.flush() # Get the voucher.id before committing

        # 2. Add the Heads
        for h in payload.heads:
            head_entry = VoucherHead(
                voucher_id=new_voucher.id,
                institution_id=current_user.institution_id,
                name=h.name,
                amount=h.amount
            )
            db.add(head_entry)

        db.commit()
        return {"status": "success", "voucher_id": new_voucher.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")