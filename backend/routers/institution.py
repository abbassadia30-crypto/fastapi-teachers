from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from backend import database  # Use relative imports for core files
from backend.dependencies import get_current_user
from backend.models.admin.institution import User, School, Academy, College
from backend.schemas.User.login import RoleUpdate

router = APIRouter(
    prefix="/institution",
    tags=["Institution Management"]
)

# --- Role Selection (Step 2 of Onboarding) ---

@router.patch("/update-role")
async def update_user_role(
        payload: RoleUpdate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # Validate allowed roles
    if payload.role not in ["admin", "teacher", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role selection")

    current_user.role = payload.role

    # Logic: If they pick admin, ensure they are flagged for the setup pathway
    if payload.role == "admin":
        current_user.has_institution = False
    else:
        # Teachers/Students are usually invited, so they might not need a 'setup'
        current_user.has_institution = True

    db.commit()
    db.refresh(current_user) # Important to get updated state

    return {
        "status": "success",
        "role": current_user.role,
        "has_institution": current_user.has_institution,
        "institution_id": current_user.institution_id
    }

@router.post("/setup-workspace")
async def setup_workspace(
    payload: dict = Body(...), 
    db: Session = Depends(database.get_db), # Fixed reference to database
    current_user: User = Depends(get_current_user)
):
    # 1. Validation: Only 'admin' role should be creating institutions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can setup a workspace")

    # 2. Check if user already owns an institution
    if current_user.owned_institution:
        raise HTTPException(status_code=400, detail="Workspace already exists for this user")

    inst_type = payload.get("type") # 'school', 'academy', or 'college'
    
    # 3. Polymorphic Creation logic
    try:
        if inst_type == "school":
            new_inst = School(
                owner_id=current_user.id,
                name=payload.get("name"),
                principal_name=payload.get("principal_name"),
                campus=payload.get("campus"),
                address=payload.get("address"),
                email=payload.get("email")
            )
        elif inst_type == "academy":
            new_inst = Academy(
                owner_id=current_user.id,
                name=payload.get("name"),
                edu_type=payload.get("edu_type"),
                campus_name=payload.get("campus_name"),
                address=payload.get("address"),
                email=payload.get("email")
            )
        elif inst_type == "college":
            new_inst = College(
                owner_id=current_user.id,
                name=payload.get("name"),
                dean_name=payload.get("dean_name"),
                code=payload.get("code"),
                address=payload.get("address"),
                email=payload.get("email")
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid institution type")

        db.add(new_inst)
        db.flush() # Flush to get new_inst.id before final commit

        # 4. Automatically link the Admin to their new workspace
        current_user.institution_id = new_inst.id
        db.commit()
        db.refresh(new_inst)

        return {"status": "success", "message": f"{inst_type.capitalize()} created!", "institution_id": new_inst.institution_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create institution")