from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from shared.db.models.jobs import JobType


class JobCreate(BaseModel):
    type: JobType
    payload: dict[str, Any] = Field(default_factory=dict, description="Job input (e.g. text, file_path)")


class JobRead(BaseModel):
    """Response when reading a single job (status, result, etc.)."""
    

class JobListItem(BaseModel):
    """Minimal job fields for list endpoints (e.g. GET /jobs)."""
    model_config = {"from_attributes": True}

    id: int
    type: JobType
    status: str
    user_id: int
    created_at: datetime
    retries: int = 0