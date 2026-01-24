from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.routers.auth import get_current_user
from .. import models, schemas, database
from backend.database import get_db

router = APIRouter(
    prefix="/profile",
    tags=["profile Management"]
)

@router.post("/update")
def update_bio(
        bio_data: schemas.BioUpdate,
        # 🏛️ This ensures ONLY the logged-in user can update their OWN data
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(database.get_db)
):
    # Check if the user has the correct role for this institution action
    # if current_user.role != "teacher":
    #    raise HTTPException(status_code=403, detail="Not authorized")

    db_bio = db.query(models.UserBio).filter(models.UserBio.user_id == current_user.id).first()

    if db_bio:
        db_bio.full_name = bio_data.full_name
        db_bio.short_bio = bio_data.short_bio
        db_bio.custom_details = bio_data.custom_details
    else:
        db_bio = models.UserBio(
            **bio_data.model_dump(),
            user_id=current_user.id # 🏛️ Use the ID from the secure token
        )
        db.add(db_bio)

    try:
        db.commit()
        db.refresh(db_bio)
        return {"status": "success", "message": "Profile saved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")