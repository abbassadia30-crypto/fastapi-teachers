from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from backend.database import Base
import datetime
from sqlalchemy.orm import relationship

class InstitutionState(Base):
    __tablename__ = "institution_intelligence_state"

    id = Column(Integer, primary_key=True, index=True)

    # Correctly points to 'institutions.id' from your institution.py
    institution_id = Column(Integer, ForeignKey("institutions.id"), unique=True)

    full_data_blob = Column(Text, nullable=False)
    key_registry = Column(Text, nullable=False)
    last_indexed = Column(DateTime, default=datetime.datetime.utcnow)

    # Change 'institutions' to 'institution' to match your other models
    institution = relationship("Institution", back_populates="states")