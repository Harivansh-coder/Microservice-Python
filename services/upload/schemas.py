# services/upload/schemas.py
from pydantic import BaseModel
from typing import Optional


class JobStatus(BaseModel):
    """Job status response schema"""
    job_id: str
    user_id: int
    username: str
    original_filename: str
    status: str  # pending, processing, completed, failed
    file_id: Optional[str] = None
    converted_file_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class JobResponse(BaseModel):
    """Job creation response schema"""
    job_id: str
    status: str
    message: str
