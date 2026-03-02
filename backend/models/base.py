from sqlalchemy import Column, DateTime, func
from backend.database import Base

# We import Base from database.py instead of creating a new one.
# This ensures all models share the same metadata registry,
# allowing them to "see" each other in relationships.

class TimestampMixin:
    """Adds created_at and updated_at to every table automatically"""
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
