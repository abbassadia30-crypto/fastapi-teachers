from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.routers import institution
from backend.routers.auth import get_current_user

from .. import models, schemas
from main import app, get_db

router = APIRouter(
    prefix="/institution",
    tags=["Institution Management"]
)

@router.post("/create_student") # Change from @app to @router
async def create_student(
    data: schemas.AdmissionPayload, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Add this
):
    new_student = models.Student(
        name = data.name, 
        father_name = data.father_name,
        section = data.section,
        fee = data.fee,
        # Force the ID from the logged-in user, ignore the one in 'data'
        institution_id = current_user.institution_id, 
        admitted_by = current_user.email,
        extra_field = data.extra_fields,
        is_active = True
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return {"message": "Student admitted to your institution"}

@router.put("/edit_student")
async def edit_student(data: schemas.Student_update, db: Session = Depends(get_db)):
    # Fetch the existing record
    student = db.query(models.Student).filter(
        models.Student.institution_id == data.institution_id,
        models.Student.name == data.name,
        models.Student.father_name == data.father_name
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Update attributes
    student.father_name = data.father_name
    student.section = data.section
    student.fee = data.fee
    student.extra_fields = data.extra_fields
    student.is_active = True

    db.commit()
    db.refresh(student)
    return {"message": "Student updated successfully", "student": student.name}

@router.delete("/delete_student") # Changed from @app to @router
async def delete_student(data: schemas.AdmissionPayload, db: Session = Depends(get_db)):
    # 1. Find the specific student
    student = db.query(models.Student).filter(
        models.Student.institution_id == data.institution_id,
        models.Student.name == data.name,
        models.Student.father_name == data.father_name
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_active = False
    
    db.commit()
    return {"message": f"Student {data.name} has been deactivated (soft deleted)"}

@router.get("/my_students")
async def get_students(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Fetch the data into a variable first
    students = db.query(models.Student).filter(
        models.Student.institution_id == current_user.institution_id,
        models.Student.is_active == True
    ).all()

    # 2. Check if the list is empty
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this institution")
    
    # 3. Return the formatted response
    return {
        "message": "Students successfully retrieved", 
        "count": len(students),
        "institution": current_user.institution_id,
        "students": students
    }

@router.post("/add_staff", status_code=201)
async def add_staff_record(
    data: schemas.StaffCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. High-End Apps check for existing records (e.g., same phone number)
    existing_staff = db.query(models.Staff).filter(
        models.Staff.phone == data.phone,
        models.Staff.institution_id == current_user.institution_id
    ).first()
    
    if existing_staff:
        raise HTTPException(status_code=400, detail="Staff member with this phone already exists")

    try:
        new_staff = models.Staff(
            name=data.name,
            designation=data.designation,
            phone=data.phone,
            salary=data.salary,
            joining_date=data.joining_date,
            institution_id=current_user.institution_id,
            extra_details=data.extra_details # Fixed naming from your previous schema
        )
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
        return {"status": "success", "message": f"Record created for {data.name}", "id": new_staff.id}
    
    except SQLAlchemyError:
        db.rollback() # Crucial for high-end apps to prevent DB corruption
        raise HTTPException(status_code=500, detail="Database error occurred while hiring staff")

@router.get("/view_staff_ledger", response_model=schemas.StaffListResponse)
async def get_staff_records(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Optimization: Only select active records and order them by joining date
    records = db.query(models.Staff).filter(
        models.Staff.institution_id == current_user.institution_id,
        models.Staff.is_active == True
    ).order_by(models.Staff.joining_date.desc()).all()

    # Even if empty, a high-end app returns a consistent structure
    return {
        "institution_id": current_user.institution_id,
        "total_employees": len(records),
        "rows": records 
    }