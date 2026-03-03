from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from .. import database
from backend.database import get_db
from backend.models.admin.dashboard import student , Staff , teacher
from  backend.models.admin.institution import Institution
from backend.schemas.admin.dashboard import AdmissionPayload, Student_update, TeacherCreate, TeacherListResponse, StaffCreate,StaffResponse, StaffListResponse, EmployeeUpdate, StaffUpdate
from backend.models.User import User , Owner

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

    new_student = student(
        **data.dict(),
        institution_id=current_user.institution_id,
        admitted_by=current_user.user_email
    )
    db.add(new_student)
    db.commit()
    return {"status": "success", "message": "Student added to institution"}

@router.delete("/delete_student/{student_id}")
async def delete_student(
        student_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # FIX: Use 'target' instead of 'student' for the variable name
    target = db.query(student).filter(
        student.id == student_id,
        student.institution_id == current_user.institution_id
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Student record not found")

    db.delete(target) # Full removal from institution records
    db.commit()
    return {"status": "success", "message": "Student removed"}

@router.put("/edit_student/{student_id}")
async def edit_student(
        student_id: int,
        data: Student_update,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    target = db.query(student).filter(
        student.id == student_id,
        student.institution_id == current_user.institution_id
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Student not found")

    target.name = data.name
    target.father_name = data.father_name
    target.section = data.section
    target.fee = data.fee
    target.extra_fields = data.extra_fields

    db.commit()
    return {"status": "success", "message": "Update successful"}

@router.patch("/rename_section")
async def rename_section(
        old_name: str,
        new_name: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # This updates the section string for all students in that class at once
    db.query(student).filter(
        student.section == old_name,
        student.institution_id == current_user.institution_id
    ).update({"section": new_name})

    db.commit()
    return {"message": "Section renamed successfully"}

@router.get("/my_students")
async def get_students(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    students = db.query(student).filter(
        student.institution_id == current_user.institution_id,
        student.is_active == True
    ).all()

    return {
        "count": len(students),
        "students": students
    }

@router.get("/sections")
async def get_unique_sections(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # This query gets distinct section names for the logged-in user's institution
    sections = db.query(student.section).filter(
        student.institution_id == current_user.institution_id,
        student.is_active == True
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
    new_teacher = teacher(
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
    teachers = db.query(teacher).filter(
        teacher.institution_id == current_user.institution_id
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
    # Rename the variable to 'record' or 'target' to avoid shadowing the class 'teacher'
    record = db.query(teacher).filter(
        teacher.id == teacher_id,
        teacher.institution_id == current_user.institution_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Teacher record not found")

    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Teacher removed"}

@router.patch("/teacher/{teacher_id}")
async def update_teacher(
        teacher_id: int,
        data: EmployeeUpdate, # Ensure your schema includes designation
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Renamed variable to teacher_obj to avoid conflict with the model class name 'teacher'
    teacher_obj = db.query(teacher).filter(
        teacher.id == teacher_id,
        teacher.institution_id == current_user.institution_id
    ).first()

    if not teacher_obj:
        raise HTTPException(status_code=404, detail="Teacher record not found")

    # model_dump(exclude_unset=True) ensures we only update fields sent by UI
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if key == "designation":
            # Map 'designation' back to 'subject_expertise' in the DB
            setattr(teacher_obj, "subject_expertise", value)
        else:
            setattr(teacher_obj, key, value)

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


@router.get("/check-ownership")
async def check_ownership(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    🏛️ Super Console: Validates that the current user is an owner
    and returns their linked institution details.
    """

    # 1. Verify User is an Owner
    if current_user.type != "owner":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Owner role required."
        )

    # 2. Check for linked Institution
    # 🏛️ REFINED LOGIC: We look at the Owner table (which inherits from User)
    # because that is where the 'institution_id' now lives.
    owner_record = db.query(Owner).filter(Owner.id == current_user.id).first()

    # Safety check: if they have the 'owner' type but no Owner record
    if not owner_record:
        return {
            "has_institution": False,
            "institution_name": None,
            "user_role": current_user.type
        }

    # 3. Retrieve Institution Details
    # If owner_record.institution_id exists, we fetch the Institution object
    institution = None
    if owner_record.institution_id:
        institution = db.query(Institution).filter(Institution.id == owner_record.institution_id).first()

    if not institution:
        return {
            "has_institution": False,
            "institution_name": None,
            "user_role": current_user.type
        }

    # 4. Success: Return details for the Admin Portal
    return {
        "has_institution": True,
        "institution_name": institution.name,
        "institution_id": institution.id,
        "institution_uuid": institution.inst_uuid, # Useful for frontend routing
        "user_role": current_user.type,
        "full_name": current_user.user_name
    }

@router.get("/students/{section_name}")
async def get_students_by_section(
        section_name: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    🏛️ SUPER CONSOLE FETCH:
    Returns all active students for a specific section within the user's institution.
    """
    # 1. Filter by Institution ID (Security & Truth)
    # 2. Filter by Section Name
    # 3. Ensure only Active students are fetched
    students = db.query(student).filter(
        student.institution_id == current_user.institution_id,
        student.section == section_name,
        student.is_active == True
    ).order_by(student.name.asc()).all()

    if not students:
        # We return an empty list instead of an error to keep the frontend Grid stable
        return []

    return students

# Add to backend/routers/dashboard.py

@router.post("/bulk-admit-students")
async def bulk_admit_students(
        students_list: list[AdmissionPayload], # Expects a list of student objects
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        new_students = []
        for data in students_list:
            # We transform each student dict into a model instance
            student_obj = student(
                **data.dict(),
                institution_id=current_user.institution_id,
                admitted_by=current_user.user_email,
                is_active=True,
                created_at=datetime.utcnow()
            )
            new_students.append(student_obj)

        # Add all at once
        db.add_all(new_students)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully admitted {len(new_students)} students to the institution."
        }
    except Exception as e:
        db.rollback()
        print(f"Bulk Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process bulk admission")