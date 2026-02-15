from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session

from backend import database  # Use relative imports for core files
from backend.dependencies import get_current_user
from backend.models.admin.institution import  School, Academy, College
from backend.schemas.User.login import RoleUpdate
from backend.models.User import User

router = APIRouter(
    prefix="/joining",
    tags=["Institution Management"]
)

@router.put("/join_institute")
def Joining(payload: Join_institute,db: Session = Depends(database.get_db),current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.email == payload.email)