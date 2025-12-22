import os
from sqlalchemy import create_engine

# 1. Get the key we set in Render
SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')

# 2. Fix the prefix for SQLAlchemy compatibility
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Create the engine
# If no URL is found (local testing), it falls back to SQLite
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./institution.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)