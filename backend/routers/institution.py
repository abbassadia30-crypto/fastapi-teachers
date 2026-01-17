from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(
    prefix="/institution",
    tags=["Institution Management"]
)

# --- Role Selection (Step 2 of Onboarding) ---

@router.patch("/update-role")
async def update_user_role(payload: schemas.RoleUpdate, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Institution user not found")

    user.role = payload.role
    db.commit()
    return {"status": "success", "message": f"Role updated to {payload.role}"}


# --- Institution Creation (Step 3 of Onboarding) ---

@router.post("/create-school", response_model=schemas.SchoolSchema)
async def create_school(data: schemas.SchoolSchema, db: Session = Depends(database.get_db)):
    # Check if code already exists to prevent crashes
    existing = db.query(models.School).filter(models.School.institution_code == data.institution_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution code already exists")

    new_school = models.School(**data.model_dump())
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    return new_school


@router.post("/create-academy")
async def create_academy(data: schemas.AcademySchema, db: Session = Depends(database.get_db)):
    new_academy = models.Academy(**data.model_dump())
    db.add(new_academy)
    db.commit()
    db.refresh(new_academy)
    return new_academy


@router.post("/create-college")
async def create_college(data: schemas.CollegeSchema, db: Session = Depends(database.get_db)):
    new_college = models.College(**data.model_dump())
    db.add(new_college)
    db.commit()
    db.refresh(new_college)
    return new_college