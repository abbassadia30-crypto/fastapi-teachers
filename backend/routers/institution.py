from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, status
from sqlalchemy.orm import Session
from backend.routers.auth import send_email_task
from backend import database  # Use relative imports for core files
from backend.routers.auth import get_current_user
from backend.models.admin.institution import  School, Academy, College
from backend.schemas.User.login import RoleUpdate
from backend.models.User import User
from backend.models.User import User, Admin, Teacher, Student, Owner , Auth_id
from backend.models.admin.profile import Profile # Ensure this path is correct

router = APIRouter(
    prefix="/institution",
    tags=["Institution Management"]
)
# backend/routers/institution.py

@router.post("/initialize-role")
async def initialize_user_role(
        payload: RoleUpdate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    role_map = {"admin": Admin, "teacher": Teacher, "student": Student, "owner": Owner}
    new_role_type = payload.role.lower()

    # Get the ID if it exists, otherwise it stays None
    target_inst_id = getattr(current_user, "last_active_institution_id", None)

    RoleClass = role_map[new_role_type]
    existing_role = db.query(RoleClass).filter(RoleClass.id == current_user.id).first()

    if not existing_role:
        from sqlalchemy import insert
        # Even if target_inst_id is None, this will now succeed because we made the column nullable
        stmt = insert(RoleClass).values(id=current_user.id, institution_id=target_inst_id)
        db.execute(stmt)

        # Initialize the professional profile
        new_profile = Profile(professional_title=f"New {new_role_type.capitalize()}")
        setattr(new_profile, f"{new_role_type}_id", current_user.id)
        db.add(new_profile)

    current_user.type = new_role_type
    db.commit()

    return {"status": "success", "role": new_role_type}

@router.patch("/update-role")
async def update_user_role(
        payload: RoleUpdate,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    target_inst_id = current_user.last_active_institution_id
    new_role_type = payload.role.lower()

    # 1. Ensure role record exists
    if new_role_type == "admin":
        role_cls = Admin
    elif new_role_type == "teacher":
        role_cls = Teacher
    # ... and so on

    existing = db.query(role_cls).filter_by(id=current_user.id).first()
    if not existing:
        new_role_record = role_cls(id=current_user.id, institution_id=target_inst_id)
        db.add(new_role_record)
        db.flush() # Sync with DB to get IDs ready

    # 2. Travel the user
    current_user.type = new_role_type
    db.commit()
    db.refresh(current_user)

    # 3. Use the @property for the response
    active_prof = current_user.active_profile

    return {
        "status": "success",
        "active_role": current_user.type,
        "profile": {
            "title": active_prof.professional_title if active_prof else "Member",
            "bio": active_prof.institutional_bio if active_prof else ""
        }
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

@router.get("/sync-state")
async def get_sync_state(
        background_tasks: BackgroundTasks,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Logic Gates
    if not current_user.type:
        return JSONResponse(status_code=400, content={"error": "role_missing"})

    role_col = getattr(Auth_id, f"{current_user.type}_id")
    identity = db.query(Auth_id).filter(role_col == current_user.id).first()

    if not identity:
        return JSONResponse(status_code=400, content={"error": "identity_missing"})

    # 2. Formal Email (The only communication sent now)
    background_tasks.add_task(
        send_email_task,
        current_user.user_email,
        identity.full_name,
        "Your identity verification is complete. Your institutional profile is now active."
    )

    return {
        "user_role": current_user.type,
        "institution_id": getattr(current_user, "last_active_institution_id", None),
        "full_name": identity.full_name
    }

@router.get("/verify-setup-eligibility")
async def verify_setup_eligibility(
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Check if Account exists (get_current_user already handles this via JWT)
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Check for Role
    if not current_user.type or current_user.type in ["user", "verified_user"]:
        return {
            "exists": True,
            "role_assigned": False,
            "identity_verified": False,
            "has_institution": False
        }

    # 3. Check for Identity (Auth_id table)
    role_type = current_user.type
    # Dynamically get the column (e.g., owner_id, admin_id)
    role_col = getattr(Auth_id, f"{role_type}_id")
    identity = db.query(Auth_id).filter(role_col == current_user.id).first()

    if not identity:
        return {
            "exists": True,
            "role_assigned": True,
            "role": role_type,
            "identity_verified": False,
            "has_institution": False
        }

    # 4. Check for existing Institution
    has_inst = current_user.last_active_institution_id is not None

    return {
        "exists": True,
        "role_assigned": True,
        "role": role_type,
        "identity_verified": True,
        "has_institution": has_inst,
        "full_name": identity.full_name
    }