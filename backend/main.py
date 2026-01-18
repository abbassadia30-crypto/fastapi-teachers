import os
import json
import random
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import APIRouter, FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend import schemas
from backend.models import School, Student
from backend.routers import auth, institution
from backend.schemas import RoleUpdate
from backend.models import Student
from backend import models
from backend.database import engine, SessionLocal
import resend
from . import models

models.Base.metadata.create_all(bind=engine)

router = APIRouter()

resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")

app = FastAPI()

app.include_router(auth.router)
app.include_router(institution.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

