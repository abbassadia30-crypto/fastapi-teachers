from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from backend import database  # Use relative imports for core files
from backend.dependencies import get_current_user
from backend.models.admin.institution import  School, Academy, College
from backend.schemas.User.login import RoleUpdate
from backend.models.User import User

router = APIRouter(
    prefix="/joining",
    tags=["Institution Management"]
)

@router.post("/join")
async def join_institution(
        payload: dict = Body(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    inst_ref = payload.get("inst_ref")
    join_key = payload.get("join_key")

    # 1. Find the Institution
    inst = db.query(Institution).filter(
        Institution.inst_ref == inst_ref,
        Institution.join_key == join_key
    ).first()

    if not inst:
        raise HTTPException(status_code=404, detail="Invalid Reference or Join Key")

    # 2. Check if user is already linked to ANY institution
    if current_user.institution_id:
        raise HTTPException(status_code=400, detail="You are already linked to an institution")

    # 3. Create the Role-Specific Record
    # We use the 'type' field from your User model to decide which table to join
    try:
        if current_user.type == "admin":
            from backend.models.admin.institution import Admin # Ensure imports
            new_role = Admin(user_id=current_user.id, institution_id=inst.id)

        elif current_user.type == "teacher":
            from backend.models.admin.institution import Teacher
            new_role = Teacher(user_id=current_user.id, institution_id=inst.id)

        elif current_user.type == "student":
            from backend.models.admin.institution import Student
            new_role = Student(user_id=current_user.id, institution_id=inst.id)

        else:
            raise HTTPException(status_code=400, detail="User type not eligible to join")

        # 4. Update the Base User
        current_user.institution_id = inst.id
        db.add(new_role)
        db.commit()

        return {
            "status": "success",
            "message": f"Successfully joined {inst.name}",
            "institution_name": inst.name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to link to institution")