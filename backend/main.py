import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend import models
from backend.routers import auth, dashboard, institution, ready, pay, profile
import logging
# 🏛️ PEER TIP: This stops passlib from crashing on bcrypt version checks
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# ... include routers ...

# ... (rest of your middleware and router includes)

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(pay.router)
app.include_router(profile.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fastapi-teachers.onrender.com"],  # For production, replace "*" with your app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

