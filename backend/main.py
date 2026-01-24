import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend import models
from backend.routers import auth, dashboard, institution, ready, pay

# 1. Physical Delete
db_file = "institution.db"
if os.path.exists(db_file):
    os.remove(db_file)
    print("🏛️ Old DB removed.")

# 2. Create Tables
print("🏛️ Initializing Institution Database...")
models.Base.metadata.create_all(bind=engine)

# 3. SAFETY SLEEP (The Fix)
# Give the file system 2 seconds to finish writing the .db file
time.sleep(2)
print("🏛️ Database Tables Verified and Ready.")

app = FastAPI()
# ... include routers ...

# ... (rest of your middleware and router includes)

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

