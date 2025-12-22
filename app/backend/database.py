import os
from sqlalchemy import create_engine

# Get the URL from Render Environment
uri = os.getenv("DATABASE_URL")

if uri and uri.startswith("postgres://"):
    # SQLAlchemy requires 'postgresql://' instead of 'postgres://'
    uri = uri.replace("postgres://", "postgresql://", 1)

# Fallback to local SQLite if no URL found
SQLALCHEMY_DATABASE_URL = uri or "sqlite:///./institution.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)