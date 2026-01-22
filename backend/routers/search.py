import os
import random
import resend
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv
from backend.scuirity import pwd_context, SECRET_KEY, ALGORITHM, oauth2_scheme

# Import local modules correctly
# Ensure 'models', 'schemas', and 'database' are in the same directory or adjust paths
from .. import models, schemas, database
from backend.database import get_db


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/global-search")
async def global_search(q: str, db: Session = Depends(get_db)):
    # Search Institutions
    institutions = db.query(models.Institution).filter(models.Institution.name.ilike(f"%{q}%")).all()
    # Search Users (Teachers/Students)
    users = db.query(models.User).filter(models.User.full_name.ilike(f"%{q}%")).all()

    return {
        "institutions": institutions,
        "users": users
    }