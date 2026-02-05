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

Base.metadata.drop_all(bind=engine)

Base.metadata.create_all(bind=engine)
logging.getLogger("passlib").setLevel(logging.ERROR)
os.environ["PASSLIB_BUILTIN_BCRYPT"] = "enabled"

app = FastAPI()
# ... include routers ...

# ... (rest of your middleware and router includes)

app.include_router(auth.router)
app.include_router(institution.router)
app.include_router(dashboard.router)
app.include_router(ready.router)
app.include_router(profile.router)
app.include_router(document.router)
app.include_router(central_vault)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace "*" with your app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


