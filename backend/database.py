from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 🏛️ Priority: Use PostgreSQL if available, fallback to SQLite for local testing
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Render's DATABASE_URL often starts with 'postgres://',
# but SQLAlchemy requires 'postgresql://'. This fix is essential:
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# If no DB URL is found (like on your local PC), it uses SQLite
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # check_same_thread is ONLY for SQLite
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()