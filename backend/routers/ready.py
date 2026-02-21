from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from backend import database
from backend.routers.auth import get_current_user
from backend.models.admin.institution import Institution, School, Academy, College
from backend.schemas.admin.institution import SchoolSchema, AcademySchema, CollegeSchema
from backend.models.User import User , Owner
from backend.routers.__init__ import send_push_to_user  # Import your FCM function

router = APIRouter(prefix="/ready", tags=["Institution creation"])

@router.get("/check-essentials")
async def check_essentials(
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Essential: Role Check
    if not current_user.type:
        return JSONResponse(status_code=400, content={"missing": "role"})

    # 2. Essential: Identity Check (Auth_id table)
    role_type = current_user.type
    role_col = getattr(models.Auth_id, f"{role_type}_id")
    identity = db.query(models.Auth_id).filter(role_col == current_user.id).first()

    if not identity:
        return JSONResponse(status_code=400, content={"missing": "identity"})

    # 3. Trigger "Setup Complete" Notification
    if current_user.fcm_token:
        try:
            send_push_to_user(
                current_user.fcm_token,
                "Setup Successful! 🎉",
                f"Welcome {identity.full_name}, your {role_type} workspace is ready."
            )
        except Exception as e:
            print(f"Notification Error: {e}")

    return {
        "status": "ready",
        "role": current_user.type,
        "full_name": identity.full_name
    }

import secrets
import string

@router.post("/create-school", status_code=status.HTTP_201_CREATED)
async def create_school(
        payload: SchoolSchema,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Verification Logic
    owner_record = db.query(Owner).filter(Owner.id == current_user.id).first()
    if not owner_record or owner_record.institution_id:
        raise HTTPException(status_code=400, detail="User already linked to an institution.")

    # 🏛️ 2. GENERATE CUSTOM KEYS
    # Ref: 8-digit long integer (e.g., 82749102)
    # We use a range that ensures it is always 8 digits
    generated_ref = str(secrets.randbelow(90000000) + 10000000)

    # Join Key: 10 chars (Mix of Uppercase Letters and Digits)
    alphabet = string.ascii_uppercase + string.digits
    generated_join_key = ''.join(secrets.choice(alphabet) for _ in range(10))

    # 3. Final Mapping
    new_school = School(
        name=payload.name,
        description=payload.description,
        type="school",
        address=payload.address,
        email=str(payload.email) if payload.email else None,
        principal_name=payload.principal_name,
        campus=payload.campus,
        website=payload.website,
        # 🏛️ Applied specific requirements
        inst_ref=generated_ref,
        join_key=generated_join_key
    )

    try:
        db.add(new_school)
        db.flush()

        # Establish relationships
        owner_record.institution_id = new_school.id
        current_user.last_active_institution_id = new_school.id

        db.commit()
        db.refresh(new_school)

        return {
            "status": "success",
            "institution_id": new_school.id,
            "reference_number": new_school.inst_ref,
            "admission_key": new_school.join_key
        }
    except Exception as e:
        db.rollback()
        print(f"Deployment Error: {e}")
        raise HTTPException(status_code=500, detail="Institutional keys collision. Please try again.")

@router.post("/create-academy", status_code=status.HTTP_201_CREATED)
async def create_academy(
        payload: AcademySchema,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Ownership Guard
    existing = db.query(Institution).filter(Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already owns an active institution.")

    # 2. Create the Academy
    # SQLAlchemy uses "polymorphic_identity": "academy" to map this to the academies table
    new_academy = Academy(
        owner_id=current_user.id,
        name=payload.name,
        type="academy",
        address=payload.address,
        email=payload.email,
        edu_type=payload.edu_type, # e.g., "Medical", "Technical", "Arts"
        campus_name=payload.campus_name,
        contact=payload.contact
    )

    current_user.has_institution = True
    current_user.institution_id = new_academy.id

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    db.add(new_academy )
    db.commit()
    db.refresh(new_academy )

    return {
        "status": "success",
        "message": "College/Academy registered successfully",
        "institution_id": new_academy.institution_id
    }

@router.post("/create-college", status_code=status.HTTP_201_CREATED)
async def create_college(
        payload: CollegeSchema,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Security: Check if this email already owns an institution
    existing = db.query(Institution).filter(Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already owns an active institution."
        )

    # 2. Instantiate the College polymorphic model
    new_college = College(
        owner_id=current_user.id,
        name=payload.name,
        type="college", # Matches polymorphic_identity
        address=payload.address,
        email=payload.email,
        dean_name=payload.dean_name,
        code=payload.code,
        uni=payload.uni
    )

    current_user.has_institution = True
    current_user.institution_id = new_college.id
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    db.add(new_college)
    db.commit()
    db.refresh(new_college)

    return {
        "status": "success",
        "message": "College registered under the institution successfully",
        "institution_id": new_college.institution_id
    }