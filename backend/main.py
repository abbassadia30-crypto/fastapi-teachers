import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine
from backend.models import Base
from backend.models import User, Institution, Syllabus
from backend.routers import auth, dashboard, institution, ready, profile, document
import logging
# 🏛️ PEER TIP: This stops passlib from crashing on bcrypt version checks
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

Base.metadata.create_all(bind=engine)

app = FastAPI()
# ... include routers ...

# ... (rest of your middleware and router includes)

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(profile.router)
app.include_router(document.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace "*" with your app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

