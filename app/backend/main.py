from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.backend.database import get_db
from app.backend.models import User 
from app.backend.schemas import UserSchema, LoginSchema 
from . import schemas , models
from fastapi import FastAPI
import app.backend.models as models
from app.backend.database import engine

# This creates the tables in your Render PostgreSQL database on startup
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
async def login(data: LoginSchema, db: Session = Depends(get_db)):
    # Look in the 'users' table specifically
    user = db.query(User).filter(User.email == data.email).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return {"status": "success"}

@app.post("/users", response_model=UserSchema)
def create_user(data: UserSchema, db: Session = Depends(get_db)):
    new_user = User(**data.model_dump(exclude={"id"}))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    
    # 1. Check if unique_id already exists (Existing Logic)
    if student.unique_id:
        db_student_id = db.query(models.Student).filter(models.Student.unique_id == student.unique_id).first()
        if db_student_id:
            raise HTTPException(status_code=400, detail="This Unique ID is already assigned.")

    # 2. Logic for Father's CNIC and Father's Name consistency
    if student.father_cnic: # Assuming you named the field father_cnic in schemas
        # Look for any existing student with the same Father's CNIC
        existing_father = db.query(models.Student).filter(models.Student.father_cnic == student.father_cnic).first()
        
        if existing_father:
            # If CNIC matches, but the provided Father Name is different from the one in DB
            if existing_father.father_name.strip().lower() != student.father_name.strip().lower():
                raise HTTPException(
                    status_code=400, 
                    detail=f"CNIC match found: Father's name must be '{existing_father.father_name}' for this CNIC."
                )

    # 3. Save the record if all checks pass
    new_student = models.Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

#uvicorn app.backend.main:app --host 192.168.100.67 --port 8000 --reload