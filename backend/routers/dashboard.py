from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from .. import database
from backend.database import get_db
from backend.models.admin.dashboard import student , Staff , teacher
from  backend.models.admin.institution import Institution
from backend.schemas.admin.dashboard import AdmissionPayload, Student_update, TeacherCreate, TeacherListResponse, StaffCreate,StaffResponse, StaffListResponse, EmployeeUpdate, StaffUpdate
from backend.models.User import User

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard Management"]
)

@router.post("/admit-student")
async def admit_student(
    data: AdmissionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_student = Student(
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
    data: Student_update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Security Added
):
    # Filter by ID AND institution_id to ensure ownership
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.institution_id == current_user.institution_id
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
    current_user: User = Depends(get_current_user) # Security Added
):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.institution_id == current_user.institution_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    student.is_active = False # Soft delete
    db.commit()
    return {"message": "Student deactivated"}

@router.get("/my_students")
async def get_students(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    students = db.query(Student).filter(
        Student.institution_id == current_user.institution_id,
        Student.is_active == True
    ).all()

    return {
        "count": len(students),
        "students": students
    }

@router.get("/check-ownership")
async def check_institution_ownership(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 1. Check if the user has an Owner role record
    # This is more reliable than a boolean 'has_institution'
    from backend.models.User import Owner # Ensure import is correct

    owner_record = db.query(Owner).filter(Owner.user_id == current_user.id).first()

    if not owner_record or not owner_record.institution_id:
        return {
            "has_institution": False,
            "status": "setup_required",
            "redirect": "/admin/setups/no-institution.html"
        }

    # 2. Verify the linked institution
    institution = db.query(Institution).filter(
        Institution.id == owner_record.institution_id
    ).first()

    if not institution:
        # Fallback: Record exists but institution was deleted
        return {
            "has_institution": False,
            "status": "integrity_error",
            "redirect": "/admin/setups/no-institution.html"
        }

    # 3. Success - User is a verified owner
    return {
        "has_institution": True,
        "institution_name": institution.name,
        "institution_type": institution.type,
        "role": "owner",
        "redirect": "/admin/dashboard/dashboard.html"
    }

@router.get("/sections")
async def get_unique_sections(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # This query gets distinct section names for the logged-in user's institution
    sections = db.query(Student.section).filter(
        Student.institution_id == current_user.institution_id,
        Student.is_active == True
    ).distinct().all()

    return [s[0] for s in sections] # Returns a simple list of strings

@router.post("/hire-teacher")
async def hire_teacher(
        data: TeacherCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="Institution not identified")

    # Creating a dedicated Teacher record
    new_teacher = Teacher(
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

@router.get("/teacher-list", response_model=TeacherListResponse) # Fixed Schema
async def get_teacher_list(
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    teachers = db.query(Teacher).filter(
        Teacher.institution_id == current_user.institution_id
    ).all()

    rows = []
    for t in teachers:
        rows.append({
            "id": t.id,
            "name": t.name,
            "phone": t.phone,
            "salary": t.salary,
            "joining_date": str(t.joining_date),
            "extra_details": t.extra_details or {},
            "institution_id": t.institution_id,
            "is_active": t.is_active,
            "designation": t.subject_expertise # Maps subject back to designation for UI
        })

    return {
        "institution_id": current_user.institution_id,
        "total_teachers": len(rows),
        "rows": rows
    }

# 1. DELETE Teacher
@router.delete("/teacher/{teacher_id}")
async def delete_teacher(
        teacher_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.institution_id == current_user.institution_id
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
        data: EmployeeUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    teacher = db.query(Teacher).filter(
        Teacher.id == teacher_id,
        Teacher.institution_id == current_user.institution_id
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

# 🟢 CREATE
@router.post("/Hire_staff", response_model=StaffResponse)
def hire_staff(
        staff_in: StaffCreate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    new_staff = Staff(
        **staff_in.model_dump(),
        institution_id=current_user.institution_id
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

# 🔵 READ - Optimized with the Wrapper Schema
@router.get("/Staff_list", response_model=StaffListResponse)
def get_staff_list(
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    staff_members = db.query(Staff).filter(
        Staff.institution_id == current_user.institution_id
    ).all()

    return {
        "institution_id": current_user.institution_id,
        "total_staff": len(staff_members),
        "rows": staff_members
    }

# 🟡 UPDATE - Fixed Path and Logic
@router.patch("/update_staff/{staff_id}") # Changed to lowercase 'u' for consistency
def update_staff(
        staff_id: int,
        staff_up: StaffUpdate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    staff_query = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.institution_id == current_user.institution_id
    )

    target = staff_query.first()
    if not target:
        raise HTTPException(status_code=404, detail="Staff record not found in institution")

    # update() is efficient for multiple fields
    staff_query.update(staff_up.model_dump(exclude_unset=True))
    db.commit()
    return {"status": "success", "message": "Record updated"}

# 🔴 DELETE - Fixed the double return and floating logic
@router.delete("/delete_staff/{staff_id}")
def remove_staff(
        staff_id: int,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.institution_id == current_user.institution_id
    ).first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    db.delete(staff)
    db.commit()
    return {"status": "success", "message": "Staff record deleted successfully"}