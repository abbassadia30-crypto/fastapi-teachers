from typing import List

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

@router.post("/hire-teacher")
async def hire_teacher(
        data: schemas.TeacherCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="Institution not identified")

    # Creating a dedicated Teacher record
    new_teacher = models.Teacher(
        name=data.name,
        phone=data.phone,
        salary=data.salary,
        joining_date=data.joining_date,
        subject_expertise=data.designation, # Mapping designation to expertise
        extra_details=data.extra_details,
        institution_id=current_user.institution_id
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    return {
        "status": "success",
        "message": f"Teacher {data.name} onboarded successfully",
        "id": new_teacher.id
    }

@router.get("/teacher-list", response_model=schemas.StaffListResponse)
async def get_teacher_list(
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=401, detail="Institution not identified")

    teachers = db.query(models.Teacher).filter(
        models.Teacher.institution_id == current_user.institution_id
    ).all()

    # We must transform the Teacher object to include 'designation'
    # so the schema is happy.
    rows = []
    for t in teachers:
        teacher_data = {
            "id": t.id,
            "name": t.name,
            "phone": t.phone,
            "salary": t.salary,
            "joining_date": t.joining_date,
            "extra_details": t.extra_details,
            "institution_id": t.institution_id,
            "is_active": t.is_active,
            "designation": t.subject_expertise  # This maps expertise back to designation
        }
        rows.append(teacher_data)

    return {
        "institution_id": current_user.institution_id,
        "total_staff": len(rows), # Schema expects 'total_staff', not 'total_employees'
        "rows": rows
    }

# 1. DELETE Teacher
@router.delete("/teacher/{teacher_id}")
async def delete_teacher(
        teacher_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(
        models.Teacher.id == teacher_id,
        models.Teacher.institution_id == current_user.institution_id
    ).first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher record not found")

    db.delete(teacher)
    db.commit()
    return {"status": "success", "message": "Teacher removed"}

# 2. UPDATE Teacher
@router.patch("/teacher/{teacher_id}")
async def update_teacher(
        teacher_id: int,
        data: schemas.EmployeeUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(
        models.Teacher.id == teacher_id,
        models.Teacher.institution_id == current_user.institution_id
    ).first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher record not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        # Map designation back to subject_expertise if updated
        if key == "designation":
            setattr(teacher, "subject_expertise", value)
        else:
            setattr(teacher, key, value)

    db.commit()
    return {"status": "success", "message": "Record updated"}

@router.post("/", response_model=schemas.StaffResponse)
def hire_staff(
        staff_in: schemas.StaffCreate,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # Developer Note: We spread the staff_in data and manually add institution_id
    new_staff = models.Staff(
        **staff_in.model_dump(),
        institution_id=current_user.institution_id
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

# READ: Get All Staff
@router.get("/list", response_model=List[schemas.StaffResponse])
def get_staff_list(
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Staff).filter(
        models.Staff.institution_id == current_user.institution_id
    ).all()

# UPDATE: Edit Staff Profile
@router.patch("/{staff_id}")
def update_staff(
        staff_id: int,
        staff_up: schemas.StaffUpdate,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    staff_query = db.query(models.Staff).filter(
        models.Staff.id == staff_id,
        models.Staff.institution_id == current_user.institution_id
    )
    target = staff_query.first()

    if not target:
        raise HTTPException(status_code=404, detail="Staff record not found")

    # exclude_unset=True prevents overwriting fields with None if they weren't sent
    update_data = staff_up.model_dump(exclude_unset=True)
    staff_query.update(update_data)
    db.commit()
    return {"status": "success", "message": "Staff record updated"}

# DELETE: Remove Staff
@router.delete("/{staff_id}")
def remove_staff(
        staff_id: int,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    staff = db.query(models.Staff).filter(
        models.Staff.id == staff_id,
        models.Staff.institution_id == current_user.institution_id
    ).first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    db.delete(staff)
    db.commit()
    return {"status": "success", "message": "Staff record deleted"}