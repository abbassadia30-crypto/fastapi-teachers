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
from backend.schemas.User.login import UserCreate , LoginSchema , Token , UserExistenceResponse
from backend.models.admin.institution import Institution
from backend.models.User import User , UserBan , Verification , Profile

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

    user = db.query(User).filter(User.user_email == email).first()
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



def get_verified_inst(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.institution_id:
        raise HTTPException(status_code=400, detail="User not linked to an institution")

    inst = db.query(Institution).filter(
        Institution.id == current_user.institution_id,
        Institution.is_active == True
    ).first()

    if not inst:
        raise HTTPException(status_code=403, detail="Institution suspended or invalid")

    return inst # This is now a verified Institution object

# --- Routes ---
# backend/routers/users.py

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    # The @property magic happens here
    profile = current_user.active_profile

    return {
        "username": current_user.user_name,
        "active_role": current_user.type,
        "personal_name": current_user.bio.full_name,
        # Professional data specific to the role:
        "professional_title": profile.professional_title if profile else "No Title Set",
        "institutional_bio": profile.institutional_bio if profile else ""
    }

@router.post("/signup")
async def signup(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Base query
    existing_user = db.query(User).filter(User.user_email == str(user.email)).first()
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_pwd = hash_password(user.password)

    if existing_user:
        # --- ALL THIS MUST BE INSIDE THE 'IF' ---
        v_user = db.query(Verification).filter(Verification.id == existing_user.id).first()

        if v_user and v_user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered and verified.")

        if v_user:
            v_user.otp_code = otp
            v_user.user_password = hashed_pwd
            v_user.verified_at = None

        target_name = existing_user.user_name

    else:
        # --- ALL THIS MUST BE INSIDE THE 'ELSE' ---
        new_v_user = Verification(
            user_name=user.name,
            user_email=str(user.email),
            user_password=hashed_pwd,
            phone=None,
            otp_code=otp,
            is_verified=False,
            type="verified_user"
        )
        db.add(new_v_user)
        target_name = user.name

        # --- THIS RUNS AFTER EITHER IF OR ELSE IS FINISHED ---
    db.commit()
    background_tasks.add_task(send_email_task, str(user.email), target_name, otp)
    return {"status": "success", "message": "Verification code sent to email."}

@router.post("/login", response_model=Token)
async def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    # Query through base User model
    user = db.query(User).filter(User.user_email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.user_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    # Check verification status (accessible via the linked verification table)
    v_info = db.query(Verification).filter(Verification.id == user.id).first()
    if not v_info or not v_info.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email first.")

    # Check for Bans
    ban_status = db.query(UserBan).filter(UserBan.user_id == user.id, UserBan.is_banned == True).first()
    if ban_status:
         reason = ban_status.ban_reason or "Violation of community standards"
         raise HTTPException(status_code=403, detail=f"Account suspended: {reason}")

    access_token = create_access_token(data={"sub": user.user_email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.type or "unassigned",
        "user": user.user_name,
        "institution_id": getattr(user, 'institution_id', None)
    }

@router.post("/verify-action")
async def verify_action(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")
    otp_received = payload.get("otp")
    action = payload.get("action") # 'signup' or 'reset'

    # Must query Verification to access otp_code
    v_user = db.query(Verification).filter(Verification.user_email == email).first()

    if not v_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not v_user.otp_code or v_user.otp_code != otp_received:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    temp_token = create_access_token(data={"sub": v_user.user_email})

    if action == "signup":
        v_user.is_verified = True
        v_user.verified_at = datetime.now(timezone.utc)
        v_user.otp_code = None
        msg = "Account verified successfully."
    elif action == "reset":
        v_user.otp_code = None
        msg = "OTP verified. Proceed to reset password."
    else:
        raise HTTPException(status_code=400, detail="Invalid action type")

    db.commit()
    return {"status": "success", "message": msg, "access_token": temp_token}

@router.post("/forgot-password")
async def forgot_password(payload: dict = Body(...), background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    email = payload.get("email")
    v_user = db.query(Verification).filter(Verification.user_email == email).first()

    if not v_user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    v_user.otp_code = otp
    db.commit()

    background_tasks.add_task(send_email_task, email, v_user.user_name, otp, "Password Reset Code")
    return {"message": "Reset code sent"}

@router.post("/reset-password")
async def reset_password_confirm(payload: dict = Body(...), db: Session = Depends(get_db)):
    # We query Verification to ensure we can clear the OTP
    v_user = db.query(Verification).filter(Verification.user_email == payload.get("email")).first()

    if not v_user:
        raise HTTPException(status_code=400, detail="Invalid request")

    v_user.user_password = hash_password(payload.get("new_password"))
    v_user.otp_code = None
    db.commit()
    return {"message": "Password updated successfully"}

@router.get("/sync-state", response_model=SyncStateResponse)
async def sync_user_state(
        db: Session = Depends(database.get_db),
        current_user: User = Depends(get_current_user) # Logic: Get user from token
):
    role = current_user.type # e.g., 'owner', 'admin', 'teacher', 'student'

    # 1. Check for the Identity Anchor
    has_profile = False
    if role and role != "verified_user":
        # Look for a record where [role]_id matches the current_user.id
        # Example: getattr(Profile, "teacher_id")
        profile = db.query(Profile).filter(
            getattr(Profile, f"{role}_id") == current_user.id
        ).first()
        has_profile = profile is not None

    # 2. Return data exactly as checking.js expects
    return {
        "user_role": role,
        "institution_id": current_user.last_active_institution_id,
        "has_identity": has_profile
    }