from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    uploaded_by_user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
