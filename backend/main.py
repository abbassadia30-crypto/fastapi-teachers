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

@app.post("/students/admit")

async def admit_student(payload: schemas.AdmissionPayload, db: Session = Depends(get_db)):

    # Validate institution exists

    inst = db.query(models.Institution).filter(models.Institution.id == payload.institution_id).first()

    if not inst:

        raise HTTPException(status_code=404, detail="Institution not found")



    new_student = models.Student(

        name=payload.name,

        father_name=payload.father_name,

        section=payload.section,

        fee=payload.fee,

        admitted_by=payload.admitted_by,

        institution_id=payload.institution_id,

        extra_fields=payload.extra_fields # Pydantic dict converts to JSON automatically

    )

   

    db.add(new_student)

    db.commit()

    db.refresh(new_student)

    return {"status": "success", "student_id": new_student.id}



@app.get("/institutions/{inst_id}/students")

async def get_institution_students(inst_id: int, db: Session = Depends(get_db)):

    students = db.query(models.Student).filter(models.Student.institution_id == inst_id).all()

    return students



# --- User Management ---



@app.get("/users/me")

async def get_current_user_profile(email: str, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:

        raise HTTPException(status_code=404, detail="User not found")

    return user