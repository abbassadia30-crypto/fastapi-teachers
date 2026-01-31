from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from ..models.admin.institution import Institution, User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/global-search")
async def global_search(q: str, db: Session = Depends(get_db)):
    # Search Institutions
    institutions = db.query(Institution).filter(Institution.name.ilike(f"%{q}%")).all()
    # Search Users (Teachers/Students)
    users = db.query(User).filter(User.name.ilike(f"%{q}%")).all()

    return {
        "institutions": institutions,
        "users": users
    }