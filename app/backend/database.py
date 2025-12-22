from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔴 Change credentials only if needed
DATABASE_URL = "postgresql://postgres:0824728@localhost:5432/myapp"

engine = create_engine(
    DATABASE_URL,
    echo=False   # shows SQL logs (good for debugging)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
