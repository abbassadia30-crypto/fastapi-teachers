from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from .. import models, schemas, database
from backend.database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard Management"]
)

@router.post("/admit-student")
async def admit_student(
    data: schemas.AdmissionPayload,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    new_student = models.Student(
        **data.dict(),
        institution_id=current_user.institution_id,
        admitted_by=current_user.email
    )
    db.add(new_student)
    db.commit()
    return {"status": "success", "message": "Student added to institution"}

@router.put("/edit_student/{student_id}")
async def edit_student(
    student_id: int, 
    data: schemas.Student_update, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Security Added
):
    # Filter by ID AND institution_id to ensure ownership
    student = db.query(models.Student).filter(
        models.Student.id == student_id,
        models.Student.institution_id == current_user.institution_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your institution")

    student.name = data.name
    student.father_name = data.father_name
    student.section = data.section
    student.fee = data.fee
    student.extra_fields = data.extra_fields

    db.commit()
    return {"message": "Update successful"}

@router.delete("/delete_student/{student_id}")
async def delete_student(
    student_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Security Added
):
    student = db.query(models.Student).filter(
        models.Student.id == student_id,
        models.Student.institution_id == current_user.institution_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    student.is_active = False # Soft delete
    db.commit()
    return {"message": "Student deactivated"}

@router.get("/my_students")
async def get_students(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    students = db.query(models.Student).filter(
        models.Student.institution_id == current_user.institution_id,
        models.Student.is_active == True
    ).all()

    return {
        "count": len(students),
        "students": students
    }

@router.get("/check-ownership")
async def check_institution_ownership(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    # If the boolean flag is False, we don't even need to query the Institutions table
    if not current_user.has_institution:
        return {
            "has_institution": False,
            "redirect": "/admin/setups/no-institution.html"
        }

    # If True, get the details for the frontend
    institution = db.query(models.Institution).filter(
        models.Institution.owner_id == current_user.id
    ).first()

    return {
        "has_institution": True,
        "institution_name": institution.name if institution else "My Institution",
        "institution_type": institution.type if institution else "school",
        "redirect": "/admin/dashboard.html"
    }

@router.get("/sections")
async def get_unique_sections(
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    # This query gets distinct section names for the logged-in user's institution
    sections = db.query(models.Student.section).filter(
        models.Student.institution_id == current_user.institution_id,
        models.Student.is_active == True
    ).distinct().all()

    return [s[0] for s in sections] # Returns a simple list of strings

@router.post("/hire-staff")
async def hire_staff(
        data: schemas.StaffCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="Institution ID required")

    # Creating the record based on your Staff table
    new_staff = models.Teacher(
        name=data.name,
        designation=data.designation,
        phone=data.phone,
        salary=data.salary,
        joining_date=data.joining_date,
        extra_details=data.extra_details,
        institution_id=current_user.institution_id
    )

    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    return {
        "status": "success",
        "message": f"Faculty member {data.name} onboarded.",
        "id": new_staff.id
    }

@router.get("/teacher-list", response_model=schemas.StaffListResponse)
async def get_teacher_list(
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=401, detail="Institution not identified")

    # Since models are split, we query the Teacher table directly
    # No need for .ilike("%teacher%") anymore as this table ONLY has teachers
    teachers = db.query(models.Teacher).filter(
        models.Teacher.institution_id == current_user.institution_id
    ).all()

    print(f"DEBUG: Found {len(teachers)} teachers for institution {current_user.institution_id}")

    return {
        "institution_id": current_user.institution_id,
        "total_employees": len(teachers),
        "rows": teachers
    }