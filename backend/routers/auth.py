import os
import random
import resend
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv
from backend.scuirity import pwd_context, SECRET_KEY, ALGORITHM, oauth2_scheme
from .. import database
from backend.database import get_db
from ..schemas.user.login import UserCreate , LoginSchema , Token
from ..models.admin.institution import User

load_dotenv()

raw_expiry = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
ACCESS_TOKEN_EXPIRE_MINUTES = int(raw_expiry)
resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- Security Helpers ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 🏛️ Define this at the very start so it's resolved for the whole function
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        # 🏛️ This now works because credentials_exception is in scope
        raise credentials_exception

    user = db.query(login.User).filter(login.User.email == email).first()
    if user is None:
        raise credentials_exception

    return user

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def send_email_task(email: str, name: str, code: str, subject="Your Verification Code"):
    try:
        resend.Emails.send({
        "from": "Institution Portal <onboarding@resend.dev>",
        "to": [email],
        "subject": subject,
        "html": f"""
            <div style="font-family: sans-serif; text-align: center; padding: 20px;">
                <h2>{subject}</h2>
                <p>Hello {name}, your code is: <strong>{code}</strong></p>
            </div>
            """
        })
    except Exception as e:
        print(f"Resend Email Error: {e}")

# --- Routes ---

@router.post("/signup")
async def signup(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == str(user.email)).first()
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_pwd = hash_password(user.password)

    if existing_user:
        if existing_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered.")
        existing_user.otp_code = otp
        existing_user.password = hashed_pwd
        existing_user.otp_created_at = datetime.now(timezone.utc)
        target_name = existing_user.name
    else:
        # FIXED: Handling missing institution_id safely
        new_user = User(
            name=user.name,
            email=str(user.email), # FIXED: Convert EmailStr to str
            password=hashed_pwd,
            institution_id=user.institution_id, # This now works because it's in UserCreate
            has_institution=False, # New users start with False
            otp_code=otp,
            otp_created_at=datetime.now(timezone.utc),
            is_verified=False
        )
        db.add(new_user)
        target_name = user.name

    db.commit()
    background_tasks.add_task(send_email_task, str(user.email), target_name, otp)
    return {"status": "success", "message": "OTP sent to your email."}

@router.post("/login", response_model=Token)
async def login(
        credentials: LoginSchema,
        db: Session = Depends(database.get_db) # Ensure this is a FastAPI Depends
):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")

    # Generate Token
    access_token = create_access_token(data={"sub": user.email})

    # Return structure optimized for your JS logic
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role or "unassigned",
        "user": user.name,
        "institution_id": user.institution_id  # Returns null if not set
    }

@router.post("/forgot-password")
async def forgot_password(payload: dict = Body(...), background_tasks: BackgroundTasks = None, db: Session = Depends(database.get_db)):
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp_code, user.otp_created_at = otp, datetime.now(timezone.utc)
    db.commit()

    background_tasks.add_task(send_email_task, email, user.name, otp, "Password Reset Code")
    return {"message": "Reset code sent"}

@router.post("/reset-password")
async def reset_password_confirm(payload: dict = Body(...), db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == payload.get("email")).first()
    if not user or user.otp_code != payload.get("otp"):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.password, user.otp_code = hash_password(payload.get("new_password")), None
    db.commit()
    return {"message": "Password updated"}

@router.post("/verify-action")
async def verify_action(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")
    otp_received = payload.get("otp")
    action = payload.get("action") # 'signup' or 'reset'

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp_code or user.otp_code != otp_received:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # We need a token to secure the NEXT step
    temp_token = create_access_token(data={"sub": user.email})

    if action == "signup":
        user.is_verified = True
        user.otp_code = None 
        msg = "Account verified successfully."

    elif action == "reset":
        # We don't change the password here, just confirm the OTP is dead
        user.otp_code = None 
        msg = "OTP verified. Proceed to reset password."

    else:
        raise HTTPException(status_code=400, detail="Invalid action type")

    db.commit()
    # Return the token so the frontend can use it for the next route
    return {
        "status": "success", 
        "message": msg, 
        "access_token": temp_token
    }