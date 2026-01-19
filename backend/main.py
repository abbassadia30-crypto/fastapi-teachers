
import os
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from backend.routers import auth, dashboard, institution
from backend.database import engine
import resend
from . import models

def reset_database(engine):
    with engine.connect() as conn:
        # This tells PostgreSQL to ignore foreign key constraints during the drop
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    
    # Now recreate everything from your models
    models.Base.metadata.create_all(bind=engine)
reset_database()
router = APIRouter()

resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")

app = FastAPI()
load_dotenv()

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

