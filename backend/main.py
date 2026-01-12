import os
import random
import json
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Import your local files
from . import models, schemas
from .database import engine, SessionLocal
import resend 

# 1. Setup & Config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

# SECURITY: Use environment variables in production!
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

# 2. Helper Functions
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
                <h2 style="color: #0288d1;">{subject}</h2>
                <p>Hello {name}, your code is:</p>
                <h1 style="color: #333; font-size: 40px; letter-spacing: 5px;">{code}</h1>
                <p>This code will expire in 10 minutes.</p>
            </div>
            """
        })
    except Exception as e:
        print(f"Resend Email Error: {e}")

# 3. Authentication Routes
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
    
    # Timezone-aware expiry check
    if datetime.now(timezone.utc) > user.otp_created_at.replace(tzinfo=timezone.utc) + timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OTP expired.")

    user.is_verified, user.otp_code = True, None 
    db.commit()
    return {"status": "success", "message": "Account verified!"}

@app.post("/login")
async def login(credentials: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")
    
    return {"message": "Login successful", "user": user.name, "access_token": "token-xyz"}

# 4. Password Reset (Forgot Password)
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

# 5. Role & File Management
@app.patch("/set-role")
async def set_role(payload: dict = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.get("email")).first()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.get("role")
    db.commit()
    return {"status": "success"}