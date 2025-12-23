from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.backend.database import engine, get_db
from app.backend import models, schemas
from typing import List

# 1. Initialize Tables for the Institution
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Institution API is Online"}

@app.post("/login")
async def login(data: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return {"status": "success", "email": user.email} # Returning email to store in frontend

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, admin_email: str, db: Session = Depends(get_db)):
    # Check if student unique_id already exists
    if student.unique_id:
        existing = db.query(models.Student).filter(models.Student.unique_id == student.unique_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="This Unique ID is already assigned.")

    # Create new student linked to the admin
    new_student = models.Student(**student.model_dump(), created_by=admin_email)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=List[schemas.StudentResponse])
def get_my_students(admin_email: str, db: Session = Depends(get_db)):
    # Filter: Admins only see students they created
    return db.query(models.Student).filter(models.Student.created_by == admin_email).all()