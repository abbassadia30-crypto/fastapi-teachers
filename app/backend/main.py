from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.backend.database import engine, get_db
from app.backend import models, schemas
from typing import List

app = FastAPI()

# 1. HARD RESET LOGIC - This fixes the 'column name does not exist' error
@app.on_event("startup")
def force_sync():
    from app.backend.database import engine
    from app.backend import models
    # This deletes EVERYTHING and rebuilds it fresh
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("!!! DATABASE FULL RESET PERFORMED !!!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/users", response_model=schemas.UserSchema)
def create_user(user: schemas.UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Institution email already exists.")
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
async def login(data: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return {"status": "success", "email": user.email}

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, admin_email: str, db: Session = Depends(get_db)):
    new_student = models.Student(**student.model_dump(), created_by=admin_email)
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=List[schemas.StudentResponse])
def get_my_students(admin_email: str, db: Session = Depends(get_db)):
    return db.query(models.Student).filter(models.Student.created_by == admin_email).all()