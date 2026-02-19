import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine
from backend.models import Base # This triggers __init__.py which loads all models
import logging
import firebase_admin
from firebase_admin import messaging, credentials
from backend.routers import auth
from backend.routers import institution  # <--- Explicitly import each
from backend.routers import dashboard
from backend.routers import document
from backend.routers import profile
from backend.routers import ready
from backend.routers import central_vault

Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

app = FastAPI()

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(profile.router)
app.include_router(document.router)
app.include_router(central_vault.router)

# 1. Get absolute path to the credential file
base_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(base_dir, "firebase-adminsdk.json")

# 2. Initialize only if not already initialized (prevents errors during hot-reloads)
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully")
    except Exception as e:
        print(f"❌ Firebase init failed: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


