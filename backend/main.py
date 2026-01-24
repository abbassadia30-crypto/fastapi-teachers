
import os
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.routers import auth, dashboard, institution, ready, pay
from backend.database import engine, Base
import resend
from . import models
import bcrypt
bcrypt.__about__ = type('about', (object,), {'__version__': bcrypt.__version__})


router = APIRouter()
def reset_database():
    print("🏛️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("🏛️ Recreating all tables with new columns...")
    Base.metadata.create_all(bind=engine)

# Call this right before the app starts
reset_database()
resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")

app = FastAPI()
load_dotenv()

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(pay.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

