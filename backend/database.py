from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🏛️ Setting the path for your institution data
# Note: On Render Free Tier, this file will be wiped whenever the app restarts
# unless you use a "Render Blueprint" with a Persistent Disk.
SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

# 🏛️ Professional Developer Fix:
# We must pass connect_args directly into the engine here.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
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