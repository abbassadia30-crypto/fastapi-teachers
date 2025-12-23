from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.backend.database import get_db, engine
from app.backend import models, schemas
from typing import List
import random
from passlib.context import CryptContext

# Security: Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# Database Sync
models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Routes ---

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = str(random.randint(100000, 999999))
    
    # Real Developer Tip: Hash the password before saving!
    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password), 
        is_verified=False,
        otp_code=otp
    )
    
    db.add(new_user)
    db.commit()
    print(f"DEBUG: OTP for {user.email} is {otp}") # View this in Render Logs
    return {"message": "Verification code sent to email"}

@app.post("/verify")
async def verify_email(data: schemas.VerifyOTP, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user or user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    user.is_verified = True
    user.otp_code = None  # Clear the code after use
    db.commit()
    return {"message": "Account verified successfully"}

@app.post("/login")
async def login(data: schemas.LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    # Check if user exists, password is correct, and account is verified
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    return {
        "status": "success", 
        "email": user.email, 
        "name": user.name,
        "token": "fake-jwt-token-for-now" # We will implement real JWT next
    }

#git add -A
#git commit -m "Full sync: $(date)"
#git push origin main