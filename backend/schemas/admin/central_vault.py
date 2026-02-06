from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from datetime import datetime

# --- Chapter & Content Models for Syllabus ---

class ChapterSchema(BaseModel):
    name: str
    topics: List[str]

class SyllabusContentSchema(BaseModel):
    title: str
    chapters: List[ChapterSchema]

# --- Main Syllabus Response Model ---

class SyllabusResponse(BaseModel):
    id: int
    name: str
    subject: str
    targets: List[str]
    content: List[SyllabusContentSchema] # Use the nested schema
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
