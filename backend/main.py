import os
import random
import json
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, SessionLocal

# Database initialization
models.Base.metadata.create_all(bind=engine)

import resend 

# 1. Configure Resend Safely
# Tip: It's better to use os.getenv("RESEND_API_KEY") and set it in Render's Environment tab
resend.api_key = os.getenv("RESEND_API_KEY", "re_48a5S3AV_5nVzDAHEr5ZoSTvso55NJRCU")

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

def send_email_task(email: str, name: str, code: str):
        try:
            resend.Emails.send({
                "from": "Starlight <onboarding@resend.dev>", 
                "to": [email],
                "subject": "Your Verification Code",
                "html": f"""
                <div style="font-family: sans-serif; text-align: center; padding: 20px; border: 1px solid #eee;">
                    <h2>Verify Your Account</h2>
                    <p>Hello {name}, your OTP is:</p>
                    <h1 style="color: #4A90E2; font-size: 40px;">{code}</h1>
                    <p>This code will expire in 10 minutes.</p>
                </div>
                """
            })
        except Exception as e:
            print(f"Resend Error: {e}")

# --- AUTH TERMINALS ---

@app.post("/signup")
async def signup(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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

# --- STUDENT MANAGEMENT ---

# File setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.join(BASE_DIR, "students_record")
os.makedirs(RECORD_DIR, exist_ok=True)

@app.post("/students", response_model=schemas.StudentResponse)
async def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.StudentRecord).filter(
        models.StudentRecord.student_name == student.student_name,
        models.StudentRecord.Father_cnic == student.father_cnic
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    db_student = models.StudentRecord(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/students")
async def get_students(db: Session = Depends(get_db)):
    return db.query(models.StudentRecord).all()

@app.post("/save-to-file")
async def save_to_file(payload: dict = Body(...)):
    try:
        filename = payload.get("filename", "unsorted").strip()
        student_data = payload.get("data", {})

        if not student_data:
            raise HTTPException(status_code=400, detail="No student data provided")

        safe_name = "".join([c for c in filename if c.isalnum() or c in ('-', '_')]).strip()
        file_path = os.path.join(RECORD_DIR, f"{safe_name}.json")

        records = []
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, "r") as f:
                records = json.load(f)
        
        records.append(student_data)

        with open(file_path, "w") as f:
            json.dump(records, f, indent=4)

        return {"status": "success", "message": f"Data added to {safe_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list-records")
async def list_records():
    files = [f.replace(".json", "") for f in os.listdir(RECORD_DIR) if f.endswith(".json")]
    return files

@app.get("/open-record/{filename}")
async def open_record(filename: str):
    file_path = os.path.join(RECORD_DIR, f"{filename}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
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
    db_student = db.query(models.StudentRecord).filter(
        models.StudentRecord.student_name == student.student_name,
        models.StudentRecord.Father_cnic == student.father_cnic
    ).first()

    if not db_student:
        raise HTTPException(status_code=404, detail="Student record not found")

    update_data = student.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)

    db.commit()
    db.refresh(db_student)
    return {"status": "success", "data": db_student}

# --- PASSWORD RESET SECTION ---

def send_reset_email_task(email: str, name: str, code: str):
    """Specific email template for password resets."""
    try:
        resend.Emails.send({
            "from": "Institution Support <onboarding@resend.dev>", 
            "to": [email],
            "subject": "Reset Your Institution Password",
            "html": f"""
            <div style="font-family: sans-serif; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #0288d1;">Password Reset Request</h2>
                <p>Hello {name},</p>
                <p>We received a request to reset your password for the institution portal. Use the code below to proceed:</p>
                <div style="background: #f4f7f6; padding: 15px; text-align: center; border-radius: 8px;">
                    <h1 style="color: #333; letter-spacing: 5px; font-size: 32px; margin: 0;">{code}</h1>
                </div>
                <p>This code will expire in 10 minutes. If you did not request this, please ignore this email.</p>
            </div>
            """
        })
    except Exception as e:
        print(f"Resend Reset Error: {e}")

@app.post("/forgot-password")
async def forgot_password(payload: dict = Body(...), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    email = payload.get("email")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        # For security, we don't always want to confirm if an email exists, 
        # but in a private institution app, it's often better to show an error.
        raise HTTPException(status_code=404, detail="Email not found in our records.")

    # Generate new OTP for reset
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp_code = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()

    if background_tasks:
        background_tasks.add_task(send_reset_email_task, user.email, user.name, otp)

    return {"status": "success", "message": "Reset code sent to your email."}

@app.post("/reset-password-confirm")
async def reset_password_confirm(data: schemas.ResetPasswordSchema, db: Session = Depends(get_db)):
    # Note: You'll need to add ResetPasswordSchema to your schemas.py
    # It should contain: email, otp, and new_password
    
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid reset code.")

    if datetime.utcnow() > user.otp_created_at + timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="Reset code expired.")

    # Update password and clear OTP
    user.password = data.new_password  # In production, use pwd_context.hash(data.new_password)
    user.otp_code = None 
    db.commit()

    return {"status": "success", "message": "Password updated successfully. You can now login."}