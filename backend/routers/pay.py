from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
import csv
import io
from fastapi.responses import StreamingResponse
from .. import models, schemas, database
from .auth import get_current_user

router = APIRouter(prefix="/pay", tags=["Finance & Payroll"])

@router.get("/search", response_model=List[schemas.PaySearchResponse])
async def search_pay_records(
    q: str = Query(""), 
    category: str = Query(...), 
    month: str = Query(...), 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    search_term = f"%{q}%"
    year, mnt = map(int, month.split("-"))
    prev_month = f"{year}-{mnt-1:02d}" if mnt > 1 else f"{year-1}-12"

    if category == "student":
        results = db.query(models.Student, models.FeeRecord).outerjoin(
            models.FeeRecord, 
            (models.Student.id == models.FeeRecord.student_id) & (models.FeeRecord.month == month)
        ).filter(
            models.Student.institution_id == current_user.institution_id,
            or_(models.Student.name.ilike(search_term), models.Student.father_name.ilike(search_term))
        ).all()

        formatted = []
        for s, fr in results:
            prev = db.query(models.FeeRecord).filter(models.FeeRecord.student_id == s.id, models.FeeRecord.month == prev_month).first()
            old_debt = prev.remaining_balance if prev else 0.0
            
            formatted.append({
                "id": s.id, "name": s.name, "father_name": s.father_name,
                "contact": (s.extra_fields or {}).get("phone", "N/A"),
                "total_amount": (s.fee or 0.0) + old_debt,
                "paid": fr.amount_paid if fr else 0.0,
                "remaining": fr.remaining_balance if fr else ((s.fee or 0.0) + old_debt),
                "status": fr.status if fr else "Unpaid"
            })
        return formatted

    # ... [Staff logic follows the exact same arrears-lookup pattern] ...

@router.post("/submit-payment")
async def submit_payment(
    payload: schemas.PaymentSubmit, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    rec_model = models.FeeRecord if payload.category == "student" else models.SalaryRecord
    fk_field = "student_id" if payload.category == "student" else "staff_id"
    profile_model = models.Student if payload.category == "student" else models.Staff

    # Security Check: Ensure person belongs to this institution
    person = db.query(profile_model).filter(profile_model.id == payload.id, profile_model.institution_id == current_user.institution_id).first()
    if not person: raise HTTPException(status_code=404, detail="Not Found")

    record = db.query(rec_model).filter(getattr(rec_model, fk_field) == payload.id, rec_model.month == payload.month).first()

    if not record:
        # Arrears Logic for New Month Creation
        year, mnt = map(int, payload.month.split("-"))
        prev_m = f"{year}-{mnt-1:02d}" if mnt > 1 else f"{year-1}-12"
        prev_rec = db.query(rec_model).filter(getattr(rec_model, fk_field) == payload.id, rec_model.month == prev_m).first()
        
        arrears = prev_rec.remaining_balance if prev_rec else 0.0
        base_amt = person.fee if payload.category == "student" else person.salary
        x
        record = rec_model(
            institution_id=current_user.institution_id, month=payload.month,
            **{fk_field: payload.id}, arrears=arrears, total_due=base_amt + arrears, amount_paid=0.0
        )
        db.add(record)
        db.flush()

    record.amount_paid += payload.amount_paid
    record.remaining_balance = record.total_due - record.amount_paid
    record.status = "Paid" if record.remaining_balance <= 0 else "Partial"
    db.commit()
    return {"status": "success", "remaining": record.remaining_balance}

@router.get("/export-records")
async def export_records(year: str, category: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # ... [CSV Export Logic provided in previous turn remains valid here] ...
    pass
    if category == "student":
        records = db.query(models.FeeRecord, models.Student).join(
            models.Student, models.FeeRecord.student_id == models.Student.id
        ).filter(
            models.FeeRecord.institution_id == current_user.institution_id,
            models.FeeRecord.month.like(f"{year}-%")
        ).all()

        # 2. Create CSV in Memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Professional Headers for easy searching/sorting
        writer.writerow(["Month", "Student ID", "Student Name", "Father Name", "Fee", "Arrears", "Total Due", "Paid", "Balance", "Status"])
        
        for rec, stu in records:
            writer.writerow([
                rec.month, stu.id, stu.name, stu.father_name, 
                rec.monthly_fee, rec.arrears, rec.total_due, 
                rec.amount_paid, rec.remaining_balance, rec.status
            ])
            # Optional: Mark as archived so they can be cleared later
            rec.is_archived = True 

        db.commit()
        
        # 3. Stream back to user phone/browser
        output.seek(0)
        return StreamingResponse(
            output, 
            media_type="text/csv", 
            headers={"Content-Disposition": f"attachment; filename={category}_records_{year}.csv"}
        )