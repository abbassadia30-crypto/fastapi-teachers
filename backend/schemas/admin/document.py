from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Literal, Dict, Any, List


class VaultUpload(BaseModel):
    name: str
    doc_type: str
    content: List[Dict[str, Any]] # Stores the nested Books/Chapters
