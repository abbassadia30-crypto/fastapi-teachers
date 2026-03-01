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
    StaffAttendanceSubmit , PendingSync
from typing import Optional
from backend.models.admin.dashboard import student as StudentModel

router = APIRouter(
    prefix="/document",
    tags=["document Management"]
)

@router.post("/vault/upload")
async def upload_to_vault(data: VaultUpload, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # 🏛️ Check if this was a resumed draft we are now finalizing
    if data.id:
        existing = db.query(Syllabus).filter(
            Syllabus.id == data.id,
            Syllabus.institution_ref == current_user.institution_id
        ).first()

        if existing:
            existing.name = data.name
            existing.subject = data.subject
            existing.targets = data.targets
            existing.content = data.content
            existing.doc_type = "syllabus" # Finalize it!
            existing.author_name = getattr(current_user, 'name', 'Admin')
            db.commit()
            return {"status": "success", "id": existing.id}

    # 🏛️ Otherwise, create a fresh entry
    new_doc = Syllabus(
        institution_ref=current_user.institution_id,
        name=data.name,
        subject=data.subject,
        targets=data.targets,
        doc_type="syllabus",
        content=data.content,
        author_name=getattr(current_user, 'name', 'Admin')
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return {"status": "success", "id": new_doc.id}

@router.delete("/pending/delete/{doc_id}")
async def delete_pending_syllabus(
        doc_id: int,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    draft = db.query(Syllabus).filter(
        Syllabus.id == doc_id,
        Syllabus.institution_ref == current_user.institution_id
    ).first()

    if not draft:
        raise HTTPException(status_code=404, detail="Syllabus not found")

    db.delete(draft)
    db.commit()
    return {"status": "success", "message": "Draft deleted"}

@router.post("/create", response_model=DateSheetResponse)
def create_datesheet(
        payload: DateSheetCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 🏛️ 1. Validation for Institution Context
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="User not linked to an institution")

    if not payload.exams:
        raise HTTPException(status_code=400, detail="Datesheet must contain at least one exam.")

    # 🏛️ 2. Creating the Instance
    new_ds = DateSheet(
        institution_ref=current_user.institution_id,
        title=payload.title,
        target=payload.target,
        # model_dump() is perfect for Pydantic v2 JSON storage
        exams=[e.model_dump() for e in payload.exams],
        # 🏛️ FIX: Use user_email instead of email
        created_by=current_user.user_email
    )

    try:
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)
        return new_ds
    except Exception as e:
        db.rollback()
        # Log specifically for Render's log stream
        print(f"DATESHEET DB ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save DateSheet to Institution records"
        )

@router.post("/pending/sync")
async def sync_pending_syllabus(
        data: PendingSync,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    # 1. Initialize as None to avoid UnboundLocalError
    existing_draft = None

    # 2. Check if we are updating an existing draft
    if data.id:
        existing_draft = db.query(Syllabus).filter(
            Syllabus.id == data.id,
            Syllabus.institution_ref == current_user.institution_id
        ).first()

        # Logic for updating if found
        if existing_draft:
            existing_draft.name = data.name
            existing_draft.subject = data.subject
            existing_draft.targets = data.targets
            existing_draft.content = data.content
            # Record who made the last edit for institutional transparency
            existing_draft.author_name = getattr(current_user, 'name', 'Staff')

            db.commit()
            return {"status": "updated", "id": existing_draft.id}

    # 3. If no ID was provided OR the ID didn't exist in our DB, create new
    new_draft = Syllabus(
        institution_ref=current_user.institution_id,
        name=data.name,
        subject=data.subject,
        targets=data.targets,
        doc_type="pending_syllabus",
        content=data.content,
        author_name=getattr(current_user, 'name', 'Staff')
    )

    db.add(new_draft)
    db.commit()
    db.refresh(new_draft)

    return {"status": "created", "id": new_draft.id}

@router.get("/pending/list")
async def get_pending_syllabuses(
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    # Fetch all documents marked as pending for this institution
    drafts = db.query(Syllabus).filter(
        Syllabus.institution_ref == current_user.institution_id,
        Syllabus.doc_type == "pending_syllabus"
    ).all()

    return drafts


@router.post("/publish", response_model=NoticeResponse)
def publish_notice(
        payload: NoticeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution not linked")

    try:
        new_notice = Notice(
            institution_ref=current_user.institution_id,
            title=payload.title,
            message=payload.message,
            language=payload.language,
            # 🏛️ FIX: Changed .email to .user_email to match your User model
            created_by=current_user.user_email
        )

        db.add(new_notice)
        db.commit()
        db.refresh(new_notice)
        return new_notice

    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR (Notice): {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save notice.")

@router.post("/finance/deploy-bulk")
async def deploy_vouchers(
        payload: BulkDeployPayload,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="Institution context missing")

    if not payload.vouchers:
        raise HTTPException(status_code=400, detail="No vouchers provided in payload")

    vouchers_to_save = []

    try:
        for draft in payload.vouchers:
            # 🏛️ Server-side sum for security (never trust the frontend for totals)
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
                # 🏛️ FIX: Changed .email to .user_email
                created_by=current_user.user_email
            )
            vouchers_to_save.append(new_v)

        # 🏛️ Efficient Bulk insert
        db.add_all(vouchers_to_save)
        db.commit()

        return {
            "status": "success",
            "count": len(vouchers_to_save),
            "message": f"Successfully deployed {len(vouchers_to_save)} vouchers to {payload.billing_period}"
        }

    except Exception as e:
        db.rollback()
        # Log error for Render debugging
        print(f"FINANCE DEPLOY ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Database integrity failure during bulk deploy")

# Inside your router in document.py
@router.post("/academic/deploy-results")
async def deploy_results(
        payload: BulkResultPayload,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    try:
        # Convert Pydantic results to a list of dicts for JSON storage
        formatted_marks = [result.model_dump() for result in payload.results]

        # 🏛️ FIX: Change 'institution_id' to 'institution_ref'
        # to match your AcademicResult model definition
        new_result = AcademicResult(
            institution_ref=current_user.institution_id, # <--- Changed this line
            exam_title=payload.exam_title,
            section_identifier=payload.class_name,
            subject_name=payload.results[0].marks[0].subject if payload.results else "N/A",
            total_marks=payload.results[0].marks[0].max if payload.results else 100,
            passing_marks=payload.results[0].marks[0].pass_mark if payload.results else 33,
            marks_data=formatted_marks,
            status="published" if not payload.is_draft else "pending"
        )

        db.add(new_result)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        # This print will show the real error in your Render logs
        print(f"DEPLOY ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pending-marksheets")
async def get_pending_marksheets(
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    # Single bulk fetch: Source of Truth (Institution) + State (Pending)
    marksheets = db.query(MarksheetLog).filter(
        MarksheetLog.institution_id == current_user.institution_id,
        MarksheetLog.status == "pending"  # Only fetch what needs action
    ).order_by(MarksheetLog.created_at.desc()).all()

    return marksheets

@router.patch("/academic/finalize-results")
async def finalize_results(
        exam_title: str,
        class_name: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    inst_id = getattr(current_user, 'institution_id', None) or getattr(current_user, 'last_active_institution_id', None)

    # Update all matching records
    results = db.query(AcademicResult).filter(
        AcademicResult.institution_ref == inst_id,
        AcademicResult.exam_title == exam_title,
        AcademicResult.target_class == class_name,
        AcademicResult.status == "DRAFT"
    ).all()

    if not results:
        raise HTTPException(status_code=404, detail="No draft found")

    for r in results:
        r.status = "PUBLISHED"

    db.commit()
    return {"status": "success", "message": "Marked as Completed"}

@router.post("/papers/save-vault")
async def save_to_vault(
        payload: PaperCreate,
        paper_id: Optional[int] = None, # FastAPI will pick this from URL ?paper_id=...
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    inst_id = getattr(current_user, 'institution_id', None)
    if not inst_id:
        raise HTTPException(status_code=403, detail="Institution not found for user")

    blueprint_data = [block.model_dump() for block in payload.blueprint]

    if paper_id:
        existing = db.query(PaperVault).filter(PaperVault.id == paper_id, PaperVault.institution_ref == inst_id).first()
        if existing:
            existing.subject = payload.subject
            existing.target_class = payload.target_class
            existing.paper_type = payload.paper_type
            existing.duration = payload.duration
            existing.language = payload.language
            existing.content_blueprint = blueprint_data
            existing.total_marks = payload.total_marks
            db.commit()
            return {"status": "updated", "paper_id": existing.id}

    # Creating New if no ID or ID not found
    new_paper = PaperVault(
        institution_ref=inst_id,
        subject=payload.subject,
        target_class=payload.target_class,
        paper_type=payload.paper_type,
        duration=payload.duration,
        language=payload.language,
        content_blueprint=blueprint_data,
        total_marks=payload.total_marks,
        created_by=current_user.user_email,
        status="pending"
    )
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)
    return {"status": "created", "paper_id": new_paper.id}


@router.get("/papers/vault-list")
async def get_vault_papers(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    inst_id = getattr(current_user, 'institution_id', None)
    if not inst_id:
        raise HTTPException(status_code=403, detail="Not linked to institution")

    # FIX: Change 'is_published == False' to 'status == "pending"'
    papers = db.query(PaperVault).filter(
        PaperVault.institution_ref == inst_id,
        PaperVault.status == "pending"
    ).all()

    return papers

@router.put("/papers/mark-taken/{paper_id}")
async def mark_paper_as_taken(
        paper_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    inst_id = getattr(current_user, 'institution_id', None)
    paper = db.query(PaperVault).filter(
        PaperVault.id == paper_id,
        PaperVault.institution_ref == inst_id
    ).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper.status = "taken"  # Moving it out of the "Pending" list
    db.commit()
    return {"status": "success", "message": "Paper marked as taken"}

@router.delete("/papers/delete/{paper_id}")
async def delete_paper(
        paper_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    paper = db.query(PaperVault).filter(PaperVault.id == paper_id).first()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if the user belongs to the same institution
    if paper.institution_ref != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Unauthorized deletion attempt")

    try:
        db.delete(paper)
        db.commit()
        return {"status": "success", "message": "Paper removed from vault"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit")
async def submit_attendance(
        payload: AttendanceSubmit,
        db: Session = Depends(get_db),
        current_user: Any = Depends(get_current_user)
):
    try:
        # 🏛️ The Institution ID is our absolute Source of Truth
        inst_id = current_user.institution_id

        if not inst_id:
            raise HTTPException(status_code=403, detail="Institution context missing")

        # 1. Save the complete snapshot to the Log
        # This includes all students (registered & manual) in the 'attendance_data' JSON field
        new_log = AttendanceLog(
            institution_id=inst_id,
            section_identifier=payload.section_id,
            log_date=payload.date,
            category=payload.type,
            # model_dump() converts the Pydantic list into a JSON-compatible format
            attendance_data=[e.model_dump() for e in payload.data],
            p_count=len([x for x in payload.data if x.status == 'P']),
            a_count=len([x for x in payload.data if x.status == 'A']),
            l_count=len([x for x in payload.data if x.status == 'L'])
        )

        db.add(new_log)
        db.commit() # Commit here; no need to touch individual_attendance

        return {"status": "success", "log_id": new_log.id}

    except Exception as e:
        db.rollback()
        # Log specifically for Render debugging
        print(f"ATTENDANCE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save institutional record")

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
