from json import load
import os
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import auth, institution
from backend import models
from backend.database import engine
import resend
from . import models

models.Base.metadata.create_all(bind=engine)

router = APIRouter()

resend.api_key = os.getenv("RESEND_API_KEY", "your_key_here")

app = FastAPI()
load_dotenv()

app.include_router(auth.router)
app.include_router(institution.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

