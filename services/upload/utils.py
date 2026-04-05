# services/upload/utils.py
import logging
from fastapi import UploadFile, HTTPException
from datetime import datetime
import uuid
from db import get_db, get_gridfs_bucket
from config import settings

logger = logging.getLogger(__name__)


async def validate_mp4_file(file: UploadFile) -> bool:
    """Validate that file is MP4"""
    # Check MIME type
    if file.content_type not in ["video/mp4", "video/mpeg"]:
        return False

    # Check extension
    if not file.filename.lower().endswith(('.mp4', '.mpeg')):
        return False

    return True


async def store_file_in_gridfs(file: UploadFile, metadata: dict) -> str:
    """Store file in MongoDB GridFS"""
    gridfs_bucket = get_gridfs_bucket()
    file_id = await gridfs_bucket.upload_from_stream(
        file.filename,
        file.file,
        metadata=metadata
    )
    return str(file_id)


async def create_job(job_data: dict) -> str:
    """Create conversion job in database"""
    db = get_db()
    job_id = str(uuid.uuid4())
    job_data["job_id"] = job_id
    job_data["created_at"] = datetime.utcnow().isoformat()
    job_data["updated_at"] = datetime.utcnow().isoformat()

    await db.jobs.insert_one(job_data)
    return job_id
