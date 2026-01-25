from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pydantic import BaseModel
from sqlalchemy.orm.attributes import flag_modified

from . import auth
from .. import models, database, schemas
from .auth import get_current_user
from ..database import get_db
from ..schemas import ProfileOut

router = APIRouter(prefix="/profile", tags=["Profile"])

# 🏛️ SCHEMAS MUST BE DEFINED FIRST
class BioUpdate(BaseModel):
    full_name: str
    short_bio: Optional[str] = None
    custom_details: Optional[Dict[str, str]] = {}

@router.get("/me")
def get_my_bio(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()
    if not bio:
        return {"full_name": "", "short_bio": "", "custom_details": {}}
    return bio

# 🏛️ 2. POST route to SAVE data (Body required)
@router.post("/update")
def update_bio(
        bio_data: BioUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    db_bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()

    if db_bio:
        db_bio.full_name = bio_data.full_name
        db_bio.short_bio = bio_data.short_bio
        db_bio.custom_details = bio_data.custom_details
        flag_modified(db_bio, "custom_details")
    else:
        db_bio = models.UserBio(
            full_name=bio_data.full_name,
            short_bio=bio_data.short_bio,
            custom_details=bio_data.custom_details,
            user_id=current_user.id
        )
        db.add(db_bio)

    try:
        db.commit()
        return {"status": "success", "message": "Institution profile updated"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save to database")

@router.get("/me", response_model=schemas.ProfileOut)
async def get_my_profile(
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        # Return empty structure if not created yet
        return {"full_name": "", "short_bio": "", "custom_details": {}}
    return profile

# 🏛️ POST: Update/Create My Profile (Private)
@router.post("/update")
async def update_profile(
        data: schemas.ProfileUpdate,
        current_user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(get_db)
):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()

    if profile:
        profile.full_name = data.full_name
        profile.short_bio = data.short_bio
        profile.custom_details = data.custom_details
    else:
        new_profile = models.Profile(**data.dict(), user_id=current_user.id)
        db.add(new_profile)

    db.commit()
    return {"message": "Institution profile updated successfully"}

# 🏛️ GET: Global Search (Public)
@router.get("/profiles/all", response_model=list[ProfileOut])
def get_all_profiles(db: Session = Depends(get_db)):
    # 🏛️ Real Dev Tip: In a large app, we would add .limit(20) here
    return db.query(models.Profile).all()