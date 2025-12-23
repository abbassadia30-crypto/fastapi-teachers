from fastapi import FastAPI, Depends
from app.backend.database import engine, Base
from app.backend import models

# This line creates the tables in PostgreSQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ... (rest of your routes)