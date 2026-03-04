import os
from fastapi import FastAPI , Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine
from backend.models import Base # This triggers __init__.py which loads all models
import logging
from backend.routers import auth
from backend.routers import institution  # <--- Explicitly import each
from backend.routers import dashboard
from backend.routers import document
from backend.routers import profile
from backend.routers import ready
from backend.routers import central_vault
from backend.routers import scanner
from backend.routers import state
import firebase_admin
from firebase_admin import auth, credentials
import json
from backend.routers import auth, institution, profile # Your actual router paths
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from backend.routers.auth import get_current_user

Base.metadata.create_all(bind=engine)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

# 1. PLACE IT HERE (Global Scope)
def init_firebase():
    if not firebase_admin._apps:
        # We look for the Environment Variable you set in Render
        cred_json = os.getenv("FIREBASE_JSON")
        if cred_json:
            try:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized via Env Var")
            except Exception as e:
                print(f"❌ Firebase Init Error: {e}")
        else:
            print("⚠️ FIREBASE_JSON not found. Notifications will fail.")

# Execute immediately on startup
init_firebase()

app = FastAPI(title="Starlight Institution Manager")

# Include your routers below
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# ... rest of your code

app = FastAPI(title="Starlight Institution Manager")

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(profile.router)
app.include_router(document.router)
app.include_router(central_vault.router)
app.include_router(scanner.router)
app.include_router(state.router)

@app.get("/")
async def health_check():
    # This tells Render "I am alive and ready for Starlight!"
    return {"status": "online", "service": "Starlight Super Console"}

@app.get("/dashboard")
async def get_dashboard_data():
    return {
        "institution_name": "Starlight Super Console",
        "status": "Operational",
        "active_challenges": 12
    }

class FCMUpdate(BaseModel):
    fcm_token: str

# 2. THE CRITICAL SYNC ENDPOINT
@app.patch("/auth/update-fcm")
async def update_fcm_token(data: FCMUpdate, current_user = Depends(get_current_user)):
    # Logic to save the token to your 'starlight_u7dv' database
    # This must succeed before the user moves to the dashboard
    success = await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"fcm_token": data.fcm_token}}
    )
    if not success:
        raise HTTPException(status_code=500, detail="Database update failed")
    return {"status": "success"}

@app.get("/dashboard/check-ownership")
async def check_ownership(current_user = Depends(get_current_user)):
    # Your logic to find if they have an 'institution' [cite: 2025-12-21]
    institution = await db.institutions.find_one({"owner_id": current_user.id})
    if institution:
        return {
            "has_institution": True,
            "institution_name": institution["name"],
            "institution_id": str(institution["_id"])
        }
    return {"has_institution": False}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


