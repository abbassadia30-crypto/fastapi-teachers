from database import engine, Base
# Import all your models here so SQLAlchemy knows which tables to create
from models import Student 

def reset_database():
    print("⚠️  Warning: This will delete all institution records!")
    
    # 1. Drop all existing tables
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    # 2. Create tables again with the new schema (new columns like CNIC/Roll)
    print("Creating new tables based on updated models...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database has been reset and updated successfully!")

if __name__ == "__main__":
    reset_database()