import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🏛️ Get the URL from Render's Environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Handle the SQLite fallback for local testing
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

# 🏛️ Real Developer Setup: Handle SSL for Production
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={
            "sslmode": "require"  # 🏛️ This fixes the "Closed Unexpectedly" error
        }
    )
else:
    # SQLite setup
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)