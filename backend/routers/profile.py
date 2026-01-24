from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pydantic import BaseModel
from .. import models, database
from .auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

# 🏛️ SCHEMAS MUST BE DEFINED FIRST
class BioUpdate(BaseModel):
    full_name: str
    short_bio: Optional[str] = None
    custom_details: Optional[Dict[str, str]] = {}

# 🏛️ NOW THE ROUTES CAN USE THEM
@router.get("/me")
def get_my_bio(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()
    if not bio:
        return {"full_name": "", "short_bio": "", "custom_details": {}}
    return bio

@router.post("/update")
def update_bio(
        bio_data: BioUpdate,  # Now 'BioUpdate' is recognized!
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    db_bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()

    if db_bio:
        db_bio.full_name = bio_data.full_name
        db_bio.short_bio = bio_data.short_bio
        db_bio.custom_details = bio_data.custom_details
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