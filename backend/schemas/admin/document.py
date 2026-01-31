from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List


class VaultUpload(BaseModel):
    name: str
    doc_type: str
    content: List[Dict[str, Any]] # Stores the nested Books/Chapters
    model_config = ConfigDict(from_attributes=True)