from fastapi import UploadFile
from pydantic import BaseModel, Field, constr
from datetime import datetime
from typing import List, Optional

MAX_NAME_LENGTH = 50


class AudioFileCreate(BaseModel):
    name: constr(max_length=MAX_NAME_LENGTH) = Field(..., example="My Audio Track")


class AudioFileResponse(AudioFileCreate):
    id: int
    user_id: int
    path: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AudioFileListResponse(BaseModel):
    items: List[AudioFileResponse]
    count: int


class MultiFileUpload(BaseModel):
    files: List[UploadFile] = Field(
        ...,
        description="List of audio files to upload"
    )
    default_name: Optional[constr(max_length=MAX_NAME_LENGTH)] = Field(
        None,
        description="Default name prefix for files (optional)",
        example="Recording"
    )


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
