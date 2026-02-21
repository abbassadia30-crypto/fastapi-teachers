import os
from fastapi import FastAPI
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

Base.metadata.create_all(bind=engine)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

import os
import json
import firebase_admin
from fastapi import FastAPI
from firebase_admin import credentials
from backend.routers import auth, institution, profile # Your actual router paths

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


