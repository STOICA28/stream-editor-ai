from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    status: str
    source_video_path: str | None
    created_at: datetime
    updated_at: datetime

class MediaImportRequest(BaseModel):
    source_path: str
