from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from backend import database  # Use relative imports for core files
from backend.dependencies import get_current_user
from backend.models.admin.institution import  School, Academy, College
from backend.schemas.User.login import RoleUpdate
from backend.models.User import User

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

    current_user.has_institution = False

    db.commit()
    db.refresh(current_user) # Important to get updated state

    return {
        "status": "success",
        "role": current_user.role,
        "has_institution": current_user.has_institution,
        "institution_id": current_user.institution_id
    }

import string
import random
from backend.models.admin.institution import Institution # Base class

def generate_inst_ref():
    return "".join(random.choices(string.digits, k=8))

def generate_join_key():
    chars = string.ascii_uppercase + string.digits
    return f"{''.join(random.choices(chars, k=3))}-{''.join(random.choices(chars, k=3))}"

@router.post("/setup-workspace")
async def setup_workspace(
        payload: dict = Body(...),
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can setup a workspace")

    # Check if user is already an owner
    if current_user.owned_institution:
        raise HTTPException(status_code=400, detail="Workspace already exists for this user")

    # --- GENERATE UNIQUE PUBLIC KEYS ---
    new_ref = generate_inst_ref()
    new_key = generate_join_key()

    inst_type = payload.get("type")

    try:
        # Prepare common data
        common_data = {
            "owner_id": current_user.id,
            "name": payload.get("name"),
            "address": payload.get("address"),
            "email": payload.get("email"),
            "inst_ref": new_ref,    # The 8-digit search ID
            "join_key": new_key,    # The secret OTP key
            "is_active": True
        }

        if inst_type == "school":
            new_inst = School(**common_data,
                              principal_name=payload.get("principal_name"),
                              campus=payload.get("campus"))
        elif inst_type == "academy":
            new_inst = Academy(**common_data,
                               edu_type=payload.get("edu_type"),
                               campus_name=payload.get("campus_name"))
        elif inst_type == "college":
            new_inst = College(**common_data,
                               dean_name=payload.get("dean_name"),
                               code=payload.get("code"))
        else:
            raise HTTPException(status_code=400, detail="Invalid institution type")

        db.add(new_inst)
        db.flush()

        current_user.institution_id = new_inst.id
        db.commit()

        # Return the public keys to the frontend so the Admin can share them
        return {
            "status": "success",
            "message": f"{inst_type.capitalize()} created!",
            "inst_ref": new_ref,
            "join_key": new_key
        }

    except Exception as e:
        db.rollback()
        # In a real app, log the error 'e' here
        raise HTTPException(status_code=500, detail="Failed to create institution")