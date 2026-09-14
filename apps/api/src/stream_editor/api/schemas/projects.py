from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    status: str
    source_video_path: Optional[str]
    created_at: datetime
    updated_at: datetime

class MediaImportRequest(BaseModel):
    source_path: str
