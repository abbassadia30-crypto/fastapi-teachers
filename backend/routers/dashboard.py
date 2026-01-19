from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.routers.auth import get_current_user
from .. import models, schemas
from backend.database import get_db

router = APIRouter(
    prefix="/institution",
    tags=["Institution Management"]
)

@router.post("/admit-student")
async def admit_student(
    data: schemas.StudentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Admission is tied to the current institution of the admin
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