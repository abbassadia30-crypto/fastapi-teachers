from backend.database import Base, engine

def reset_database():
    print("🧪 RESETTING DATABASE")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ DATABASE RESET COMPLETE")
