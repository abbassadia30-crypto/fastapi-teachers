from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.backend.database import engine, get_db
from app.backend import models, schemas

# 1. Initialize Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 2. Add Middleware (Required for your frontend to talk to the cloud)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Add a Root Route (To stop the 404 on the home page)
@app.get("/")
def read_root():
    return {"message": "Institution API is Online"}

# 4. Your Student Endpoint
@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    new_student = models.Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

# 5. Your Login Endpoint
@app.post("/login")
async def login(data: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    return {"status": "success"}

# Add this route so your Card Directory can fetch data
@app.get("/students", response_model=List[schemas.StudentResponse])
def get_all_students(db: Session = Depends(get_db)):
    # This fetches every student record from the institution database
    students = db.query(models.Student).all()
    return students