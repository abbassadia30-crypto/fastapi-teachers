import os
import random
import json
from datetime import datetime, timedelta


from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, SessionLocal

models.Base.metadata.drop_all(bind = engine)
models.Base.metadata.create_all(bind=engine)

import resend  # Add this import
import os

# 1. Configure Resend (Replace with your actual key)
resend.api_key = "re_48a5S3AV_5nVzDAHEr5ZoSTvso55NJRCU"
app = FastAPI()

# --- CORS SETTINGS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/signup")
async def signup(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # --- A. DATABASE LOGIC (Keep this as is) ---
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered.")
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        existing_user.otp_code = otp
        existing_user.otp_created_at = datetime.utcnow()
        db.commit()
        target_name = existing_user.name
    else:
        otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
        new_user = models.User(
            name=user.name, email=user.email, password=user.password, 
            otp_code=otp, otp_created_at=datetime.utcnow(), is_verified=False
        )
        db.add(new_user)
        db.commit()
        target_name = user.name

    # --- B. RESEND EMAIL LOGIC ---
    def send_email_task(email: str, name: str, code: str):
        try:
            params = {
                "from": "onboarding@resend.dev", # Use this exact sender for free tier
                "to": [email],
                "subject": "Your Verification Code",
                "html": f"""
                <div style="font-family: sans-serif; text-align: center; padding: 20px;">
                    <h2>Verify Your Account</h2>
                    <p>Hello {name}, your OTP is:</p>
                    <h1 style="color: #4A90E2; font-size: 40px; letter-spacing: 5px;">{code}</h1>
                    <p>This code will expire in 10 minutes.</p>
                </div>
                """,
            }
            resend.Emails.send(params)
        except Exception as e:
            print(f"Resend Error: {e}")

    # Add to background tasks so the user gets a fast response
    background_tasks.add_task(send_email_task, user.email, target_name, otp)

    return {
        "status": "success", 
        "message": "OTP sent! Check your email.",
        "otp_debug_only": otp 
    }
@app.post("/verify-otp/")
async def verify_otp(data: schemas.VerifyOTP, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.is_verified:
        return {"message": "Account already active."}

    # FIX: Use 'and' and parentheses for clarity
    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    if datetime.utcnow() > user.otp_created_at + timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OTP expired.")

    user.is_verified = True
    user.otp_code = None 
    db.commit()

    return {"status": "success", "message": "Verified successfully!"}
@app.post("/login")
async def login(credentials: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or user.password != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")
    return {"message": "Login successful", "user": user.name}

# --- STUDENT MANAGEMENT TERMINALS ---

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.StudentRecord).filter(
        models.StudentRecord.student_name == student.student_name,
        models.StudentRecord.Father_cnic == student.father_cnic
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    db_student = models.StudentRecord(**student.dict()) # Ensure model name matches models.py
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/students")
async def get_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

# Create the directory if it doesn't exist
RECORD_DIR = "students_record"
if not os.path.exists(RECORD_DIR):
    os.makedirs(RECORD_DIR)

if not os.path.exists(RECORD_DIR):
    os.makedirs(RECORD_DIR)

# ... (Keep existing imports and auth)

# 1. Clean Path Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.join(BASE_DIR, "students_record")
os.makedirs(RECORD_DIR, exist_ok=True)

@app.post("/save-to-file")
async def save_to_file(payload: dict = Body(...)):
    """
    Completely Flexible: Takes ANY dictionary and saves it 
    into a JSON file chosen by the user.
    """
    try:
        filename = payload.get("filename", "unsorted").strip()
        student_data = payload.get("data", {})

        if not student_data:
            raise HTTPException(status_code=400, detail="No student data provided")

        # Create path: students_record/filename.json
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('-', '_')]).strip()
        file_path = os.path.join(RECORD_DIR, f"{safe_name}.json")

        # Flexible Storage Logic
        records = []
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, "r") as f:
                records = json.load(f)
        
        records.append(student_data)

        with open(file_path, "w") as f:
            json.dump(records, f, indent=4)

        return {"status": "success", "message": f"Data added to {safe_name}"}

    except Exception as e:
        print(f"Flexible Save Error: {e}")
        raise HTTPException(status_code=500, detail="System could not write data")

@app.get("/list-records")
async def list_records():
    files = [f.replace(".json", "") for f in os.listdir(RECORD_DIR) if f.endswith(".json")]
    return files

@app.get("/open-record/{filename}")
async def open_record(filename: str):
    file_path = os.path.join(RECORD_DIR, f"{filename}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(file_path, "r") as f:
        return json.load(f) # Fixed syntax here
    
@app.get("/open-record/{filename}")
async def open_record(filename: str):
    """Reads the content of a specific student record file"""
    file_path = os.path.join(RECORD_DIR, f"{filename}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Record file not found")
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not read file")
    
@app.delete("/Delete_student")
async def delete_student(student_name: str, father_cnic: str, db: Session = Depends(get_db)):
    record = db.query(models.StudentRecord).filter(
        models.StudentRecord.student_name == student_name,
        models.StudentRecord.Father_cnic == father_cnic
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Student not found")
    
    db.delete(record)
    db.commit()
    return {"message": "Deleted successfully"}

@app.put("/Edit_student")
async def edit_student(student: schemas.UpdateStudent, db: Session = Depends(get_db)):
    # 1. Find the student using unique identifiers
    db_student = db.query(models.StudentRecord).filter(
        models.StudentRecord.student_name == student.student_name,
        models.StudentRecord.Father_cnic == student.father_cnic
    ).first()

    # 2. If not found, raise the error
    if not db_student:
        raise HTTPException(status_code=404, detail="Student record not found")

    # 3. Flexible Update Logic
    # We convert the incoming data to a dictionary and loop through it.
    # This allows it to update ANY field defined in your schema/model.
    update_data = student.dict(exclude_unset=True) # Only update fields the user actually sent
    
    for key, value in update_data.items():
        setattr(db_student, key, value)

    # 4. Save changes
    try:
        db.commit()
        db.refresh(db_student)
        return {"status": "success", "message": "Student updated successfully", "data": db_student}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")