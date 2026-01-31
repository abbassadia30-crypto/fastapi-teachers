from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
class Base(DeclarativeBase):
    pass


class Syllabus(Base):
    __tablename__ = "Syllabus"
    id = Column(Integer, primary_key=True, index=True)
    institution_ref = Column(String, ForeignKey("institutions.institution_id"))
    name = Column(String, nullable=False) # e.g., "Physics Syllabus - Grade 10"
    doc_type = Column(String) # syllabus, exam, translate, or scan
    content = Column(JSON, nullable=False)
    author_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    institution = relationship("Institution")
