import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 🏛️ Priority: Get the URL from Render Environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL:
    # Render gives 'postgres://', we need 'postgresql+psycopg://'
    # The '+psycopg' part is mandatory for Python 3.13 compatibility!
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    else:
        # Even if it's already 'postgresql://', force the '+psycopg' driver
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    # 🏛️ Local Fallback (Institution DB)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

# Engine configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # Only use check_same_thread for SQLite
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()