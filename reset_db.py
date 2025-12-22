from app.backend.database import engine, Base
from app.backend.models import User

# This will remove the old table entirely
User.__table__.drop(engine, checkfirst=True)
print("Old users table dropped.")

# This creates the new table with Name, Email, and Password
Base.metadata.create_all(bind=engine)
print("New institution users table created successfully!")