import os
from sqlalchemy import create_engine
from app.backend.database import Base, SQLALCHEMY_DATABASE_URL
from app.backend import models

def reset_database():
    print("🔄 Connecting to institution database...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    print("⚠️ Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("✅ Creating new tables with updated schemas...")
    Base.metadata.create_all(bind=engine)
    
    print("🚀 Database reset successfully! You can now redeploy.")

if __name__ == "__main__":
    reset_database()