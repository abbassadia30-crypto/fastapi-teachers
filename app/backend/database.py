import os
from sqlalchemy import create_all, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Check if we are running on Render
if os.environ.get('RENDER'):
    # Use the /tmp folder for SQLite on Render
    SQLALCHEMY_DATABASE_URL = "sqlite:////tmp/institution.db"
else:
    # Use local path for your Windows machine
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()