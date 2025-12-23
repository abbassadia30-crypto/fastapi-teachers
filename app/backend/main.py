from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Correct Imports
from app.backend.database import engine, get_db, Base
from app.backend import models, schemas

# Initialize the Database Tables for the institution
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(data: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return {"status": "success"}

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    if student.unique_id:
        db_student_id = db.query(models.Student).filter(models.Student.unique_id == student.unique_id).first()
        if db_student_id:
            raise HTTPException(status_code=400, detail="This Unique ID is already assigned.")

    if student.father_cnic:
        existing_father = db.query(models.Student).filter(models.Student.father_cnic == student.father_cnic).first()
        if existing_father:
            if existing_father.father_name.strip().lower() != student.father_name.strip().lower():
                raise HTTPException(
                    status_code=400, 
                    detail=f"CNIC match found: Father's name must be '{existing_father.father_name}'"
                )

    new_student = models.Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student