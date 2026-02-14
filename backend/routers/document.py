from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.admin.document import Syllabus, DateSheet, Notice, Voucher, AcademicResult, PaperVault, \
    IndividualAttendance, AttendanceLog
from backend.routers.auth import get_current_user, get_verified_inst
from backend.database import get_db
from backend.models.admin.institution import Institution
from backend.models.User import User
from backend.schemas.admin.document import VaultUpload, DateSheetResponse, DateSheetCreate, \
    NoticeCreate, NoticeResponse, BulkDeployPayload, BulkResultPayload, PaperCreate, AttendanceSubmit, \
    StaffAttendanceSubmit

router = APIRouter(
    prefix="/document",
    tags=["document Management"]
)

@router.post("/vault/upload")
async def upload_to_vault(data: VaultUpload, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # Corrected: model uses institution_ref
    new_doc = Syllabus(
        institution_ref=current_user.institution_id,
        name=data.name,
        subject=data.subject,
        targets=data.targets,
        doc_type=data.doc_type,
        content=data.content,
        author_name=getattr(current_user, 'name', 'Admin')
    )
    db.add(new_doc)
    db.commit()
    return {"status": "success", "id": new_doc.id}

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

@router.post("/academic/deploy-results")
async def deploy_results(
        payload: BulkResultPayload,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="Institution context required")

    db_entries = []

    for entry in payload.results:
        # 🏛️ Server-side Calculation for Integrity
        total_max = sum(m.max for m in entry.marks)
        total_obt = sum(m.obt for m in entry.marks)
        perc = (total_obt / total_max * 100) if total_max > 0 else 0

        # 🏛️ Server-side Pass/Fail check (Security Measure)
        actual_status = "PASS"
        for m in entry.marks:
            if m.obt < m.pass_mark:
                actual_status = "FAIL"
                break

        new_res = AcademicResult(
            institution_ref=current_user.institution_id,
            exam_title=payload.exam_title,
            target_class=payload.class_name,
            student_id=entry.student_id,
            student_name=entry.name,
            father_name=entry.father_name,
            marks_data=[m.model_dump() for m in entry.marks],
            percentage=round(perc, 2),
            final_status=actual_status,
            created_by=current_user.email
        )
        db_entries.append(new_res)

    try:
        # Bulk save to DB
        db.add_all(db_entries)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully published {len(db_entries)} marksheets",
            "exam": payload.exam_title
        }
    except Exception as e:
        db.rollback()
        print(f"DEPLOYMENT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Database commit failed")



@router.post("/papers/save-vault")
async def save_to_vault(
        payload: PaperCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        new_paper = PaperVault(
            institution_ref=current_user.institution_id,
            subject=payload.subject,
            target_class=payload.target_class,
            paper_type=payload.paper_type,
            duration=payload.duration,
            language=payload.language,
            content_blueprint=[block.model_dump() for block in payload.blueprint],
            total_marks=payload.total_marks,
            created_by=current_user.email
        )

        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        return {"status": "success", "paper_id": new_paper.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to sync with Vault")

@router.get("/papers/vault-list")
async def get_vault_papers(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Fetch papers specifically for this institution that aren't published yet
    papers = db.query(PaperVault).filter(
        PaperVault.institution_ref == current_user.institution_id,
        PaperVault.is_published == False
    ).order_by(PaperVault.created_at.desc()).all()
    return papers


@router.post("/submit")
async def submit_attendance(payload: AttendanceSubmit, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    try:
        # Corrected: model uses institution_id
        new_log = AttendanceLog(
            institution_id=current_user.institution_id,
            section_identifier=payload.section_id,
            log_date=payload.date,
            category=payload.type,
            attendance_data=[e.model_dump() for e in payload.data],
            p_count=len([x for x in payload.data if x.status == 'P']),
            a_count=len([x for x in payload.data if x.status == 'A']),
            l_count=len([x for x in payload.data if x.status == 'L'])
        )
        db.add(new_log)
        db.flush()

        for entry in payload.data:
            if not entry.is_manual:
                indiv = IndividualAttendance(
                    institution_id=current_user.institution_id,
                    student_id=str(entry.student_id), # model expects String FK
                    log_id=new_log.id,
                    status=entry.status,
                    date=payload.date
                )
                db.add(indiv)

        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-staff")
async def submit_staff_attendance(payload: StaffAttendanceSubmit, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # Corrected: model uses institution_id
    new_log = AttendanceLog(
        institution_id=current_user.institution_id,
        section_identifier=f"STAFF_{payload.category.upper()}",
        log_date=payload.date,
        category=payload.category,
        attendance_data=[entry.model_dump() for entry in payload.data],
        p_count=len([x for x in payload.data if x.status == 'P']),
        a_count=len([x for x in payload.data if x.status == 'A']),
        l_count=len([x for x in payload.data if x.status == 'L'])
    )
    db.add(new_log)
    db.commit()
    return {"status": "success"}
