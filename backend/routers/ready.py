from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from backend import database
from backend.routers.auth import get_current_user
from backend.models.admin.institution import Institution, School, Academy, College
from backend.schemas.admin.institution import SchoolSchema, AcademySchema, CollegeSchema
from backend.models.User import User

router = APIRouter(prefix="/ready", tags=["Institution creation"])

@router.post("/create-school", status_code=status.HTTP_201_CREATED)
async def create_school(
        payload: SchoolSchema,
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user)
):
    # 1. Validation
    existing = db.query(Institution).filter(Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already owns an institution.")

    # 2. Map payload to School Model
    new_school = School(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        type="school",
        address=payload.address,
        email=str(payload.email) if payload.email else None, # Explicitly cast to string
        principal_name=payload.principal_name,
        campus=payload.campus,
        website=payload.website
    )

    # 3. Save School first to generate its ID
    db.add(new_school)
    db.flush()  # This allows us to access new_school.id before the final commit

    # 4. Link User to the new institution
    current_user.has_institution = True
    current_user.institution_id = new_school.id

    db.commit()
    db.refresh(new_school)

    return {
        "status": "success",
        "message": "Institution registered",
        "institution_id": new_school.institution_id # This is the UUID string
    }

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