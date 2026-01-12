import os
import random
from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import your local files
from . import models, schemas
from .database import engine, SessionLocal
import resend 

# Database Setup (Warning: drop_all clears data on every restart)
# models.Base.metadata.drop_all(bind=engine) 
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# SECURITY: Set this in Render Environment Variables
resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")

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

# --- Auth Helpers using Direct Bcrypt ---
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8')[:72], 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Auth Error: {e}")
        return False

def send_email_task(email: str, name: str, code: str, subject="Your Verification Code"):
    try:
        resend.Emails.send({
            "from": "Institution Portal <onboarding@resend.dev>", 
            "to": [email],
            "subject": subject,
            "html": f"""
            <div style="font-family: sans-serif; text-align: center; padding: 20px; border: 1px solid #eee; border-radius: 15px;">
                <h2 style="color: #0288d1;">{subject}</h2>
                <p>Hello {name}, your code is:</p>
                <h1 style="color: #333; font-size: 40px; letter-spacing: 5px;">{code}</h1>
                <p>This code will expire in 10 minutes.</p>
            </div>
            """
        })
    except Exception as e:
        print(f"Resend Email Error: {e}")

# --- Authentication Routes ---
@app.post("/signup")
async def signup(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_pwd = hash_password(user.password)

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered.")
        existing_user.otp_code, existing_user.password = otp, hashed_pwd
        existing_user.otp_created_at = datetime.now(timezone.utc)
        target_name = existing_user.name
    else:
        new_user = models.User(
            name=user.name, email=user.email, password=hashed_pwd, 
            otp_code=otp, otp_created_at=datetime.now(timezone.utc), is_verified=False
        )
        db.add(new_user)
        target_name = user.name

    db.commit()
    background_tasks.add_task(send_email_task, user.email, target_name, otp)
    return {"status": "success", "message": "OTP sent to your email."}

@app.post("/verify-otp/")
async def verify_otp(data: schemas.VerifyOTP, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid code or user.")
    
    # Timezone check
    otp_time = user.otp_created_at
    if otp_time.tzinfo is None:
        otp_time = otp_time.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > otp_time + timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OTP expired.")

    user.is_verified, user.otp_code = True, None 
    db.commit()

    # Return the role so the frontend can decide where to redirect
    return {
        "status": "success", 
        "message": "Account verified!",
        "role": user.role  # Returns 'admin', 'teacher', 'student', or None
    }

@app.post("/login")
async def login(credentials: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")
    
    # We include the role in the response so the frontend knows where to send them
    return {
        "message": "Login successful", 
        "user": user.name, 
        "role": user.role,  # This will be None or empty if not set
        "access_token": "token-xyz"
    }
# --- Password Reset ---
@app.post("/forgot-password")
async def forgot_password(payload: dict = Body(...), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    email = payload.get("email")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp_code, user.otp_created_at = otp, datetime.now(timezone.utc)
    db.commit()

    background_tasks.add_task(send_email_task, email, user.name, otp, "Password Reset Code")
    return {"message": "Reset code sent"}

@app.post("/reset-password-confirm")
async def reset_password_confirm(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.get("email")).first()
    if not user or user.otp_code != payload.get("otp"):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.password, user.otp_code = hash_password(payload.get("new_password")), None
    db.commit()
    return {"message": "Password updated"}

# --- Institution Role Management ---
@app.patch("/set-role")
async def set_role(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.get("email")).first()
    if not user: 
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.get("role")
    db.commit()
    return {"status": "success"}