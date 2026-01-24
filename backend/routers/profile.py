from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pydantic import BaseModel
from .. import models, database
from .auth import get_current_user # Dependency that extracts user from JWT

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/me")
def get_my_bio(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    """Fetch the bio for the logged-in institution member"""
    bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()
    if not bio:
        return {"full_name": "", "short_bio": "", "custom_details": {}}
    return bio

@router.post("/update")
def update_bio(
        bio_data: BioUpdate,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    """Save or Update the bio for the current user"""
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