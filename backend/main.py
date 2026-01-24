
import os
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
# 1. Standard imports
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 2. Database & Model imports (CRITICAL ORDER)
from backend.database import engine, Base
from backend import models  # This must happen before create_all

# 3. Define the reset/init logic
def init_db():
    # Only delete and recreate if you are still fixing the schema
    # Once fixed, you should remove the drop_all line
    print("🏛️ Initializing Institution Database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("🏛️ Database Tables Created Successfully.")

# Execute initialization immediately
init_db()

# 4. Initialize FastAPI app
app = FastAPI()

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

