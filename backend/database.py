import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🏛️ Get the URL from Render's Environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Handle the SQLite fallback for local testing
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

# 🏛️ Real Developer Setup: Handle SSL for Production
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    # Ensure the URL uses 'postgresql://' instead of 'postgres://'
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require"
        }
    )
else:
    # SQLite setup
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# 🏛️ These are the parts that were missing!
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# This function is what auth.py is looking for
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()