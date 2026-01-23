import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

# Default to local sqlite if DATABASE_URL is missing
SQLALCHEMY_DATABASE_URL = uri or "sqlite:///./institution.db"

if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # 🏛️ Professional configuration for Render External PostgreSQL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,      # Checks if connection is valid before using it
        pool_recycle=300,        # Refreshes connections to prevent ghosting
        connect_args={
            "sslmode": "require", # 🏛️ THE KEY: This forces the SSL handshake
            "connect_timeout": 10
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()