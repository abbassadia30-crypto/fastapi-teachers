import os
import random
import json
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Assuming these files exist in your directory
from . import models, schemas
from .database import engine, SessionLocal
import resend 

# Password Hashing Configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

# Securely fetch API Key
resend.api_key = os.getenv("RESEND_API_KEY", "re_48a5S3AV_5nVzDAHEr5ZoSTvso55NJRCU")

app = FastAPI()

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

# --- UTILITY FUNCTIONS ---
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def send_email_task(email: str, name: str, code: str, subject="Your Verification Code"):
    try:
        resend.Emails.send({
            "from": "Institution Portal <onboarding@resend.dev>", 
            "to": [email],
            "subject": subject,
            "html": f"""
            <div style="font-family: sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 15px;">
                <h2 style="color: #0288d1;">Security Verification</h2>
                <p>Hello {name}, your code is:</p>
                <h1 style="color: #333; font-size: 40px; letter-spacing: 5px;">{code}</h1>
                <p>This code will expire in 10 minutes.</p>
            </div>
            """
        })
    except Exception as e:
        print(f"Resend Error: {e}")

# --- AUTHENTICATION SECTION ---

@app.post("/signup")
async def signup(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """FIXED: Now properly creates users and handles OTP logic."""
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_pwd = hash_password(user.password)

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered.")
        # Update existing unverified user
        existing_user.otp_code = otp
        existing_user.password = hashed_pwd
        existing_user.otp_created_at = datetime.utcnow()
        target_name = existing_user.name
    else:
        # Create new user
        new_user = models.User(
            name=user.name, 
            email=user.email, 
            password=hashed_pwd, 
            otp_code=otp, 
            otp_created_at=datetime.utcnow(), 
            is_verified=False
        )
        db.add(new_user)
        target_name = user.name

    db.commit()
    background_tasks.add_task(send_email_task, user.email, target_name, otp)
    return {"status": "success", "message": "OTP sent to your institutional email."}

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
    """FIXED: Uses hash verification instead of plain text comparison."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")
    
    return {
        "message": "Login successful", 
        "user": user.name, 
        "access_token": "fake-jwt-token-replace-with-real-logic"
    }

# --- STUDENT MANAGEMENT ---

# Ensure directory exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORD_DIR = os.path.join(BASE_DIR, "students_record")
os.makedirs(RECORD_DIR, exist_ok=True)

@app.post("/save-to-file")
async def save_to_file(payload: dict = Body(...)):
    """FIXED: Matches the dynamic dictionary format from our Admission Form."""
    try:
        filename = payload.get("filename", "unsorted").strip()
        student_data = payload.get("data", {})

        if not student_data:
            raise HTTPException(status_code=400, detail="No student data provided")

        # Sanitize filename
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('-', '_')]).strip()
        file_path = os.path.join(RECORD_DIR, f"{safe_name}.json")

        records = []
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, "r") as f:
                records = json.load(f)
        
        # Append timestamp to the record for institutional history
        student_data["admitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
@app.patch("/set-role")
async def set_role(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")
    role = payload.get("role")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the role in database
    user.role = role # Ensure your Model has a 'role' column
    db.commit()
    return {"status": "success", "message": f"Role updated to {role}"}