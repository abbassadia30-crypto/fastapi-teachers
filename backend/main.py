import email
from email.policy import HTTP
import os
import random
import json
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

# Internal imports
import models, schemas
from database import engine, SessionLocal

# Initialize database tables
models.Base.metadata.create_all(bind=engine)

# 1. FastAPI-Mail Configuration
conf = ConnectionConfig(
    MAIL_USERNAME = "abbassadia30@gmail.com",
    MAIL_PASSWORD = "wvcz uopu bgir hzev", 
    MAIL_FROM = "abbassadia30@gmail.com", # Sender email
    MAIL_FROM_NAME = "Starlight Support",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

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
    # 1. Validation Checks (Important: Use .first())
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    if db.query(models.User).filter(models.User.name == user.name).first():
        raise HTTPException(status_code=400, detail="Username already taken.")

    # 2. Generate OTP
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])

    # 3. HTML Template
    html_content = f"""
    <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h2>Verify your Starlight Account</h2>
            <p>Your verification code is: <b>{otp}</b></p>
        </body>
    </html>
    """
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=user.password, 
        otp_code=otp,
        otp_created_at=datetime.utcnow(),
        is_verified=False
    )
    db.add(new_user)
    db.commit()

    # 5. Send Email
    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[user.email],
        body=html_content,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)

    return {"message": "OTP sent successfully"}

@app.post("/verify-otp/")
async def verify_otp(data: schemas.VerifyOTP, db: Session = Depends(get_db)):
    # 1. Find the pending record
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="No signup request found for this email.")

    # 2. Check if already verified
    if user.is_verified:
        return {"message": "Account already active. Please login."}

    # 3. Check OTP and Expiry
    if user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    if datetime.utcnow() > user.otp_created_at + timedelta(minutes=10):
        # If expired, delete the pending record so they can try again fresh
        db.delete(user)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Please sign up again.")

    # 4. SUCCESS: Now "Create" the user by marking them verified
    user.is_verified = True
    user.otp_code = None # Clean up
    db.commit()

    return {"message": "User created and verified successfully!"}

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
async def create_student(student: schemas.StudentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
  
  if db.query(models.StudentRecord).filter(models.StudentRecord.student_name == student.student_name).first():
    if db.query(models.StudentRecord).filter(models.StudentRecord.Father_cnic != student.father_cnic )
        raise HTTPException(status_code=403 , detail="Enter correct Father and student name ")  
    db_student = models.Student(**student.dict())
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
async def delete_student(student : schemas.StudentCreate , db : Session = Depends(get_db()) ):
    if db.query(models.StudentRecord).filter(models.StudentRecord.Father_cnic != student.father_cnic & models.StudentRecord.student_name != student.student_name ).first():
          raise HTTPException(status_code=402 , detail="It is already deleted")
    
    db.delete(student)
    db.commit()

@app.put("Edit_student")
async def edit_student(student : schemas.UpdateStudent  ,  db : Session = Depends(get_db)):
    students = db.query(models.StudentRecord).filter(models.StudentRecord.Father_cnic != student.father_cnic & models.StudentRecord.student_name != student.student_name ).first()
    if students:
        raise HTTPException(status_code=402 , detail="Student does not exist")
    
    for row in student:
       students.row = student.row
    
