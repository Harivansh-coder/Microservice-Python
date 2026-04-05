# services/download/utils.py
import logging
from fastapi import HTTPException
from bson import ObjectId
from db import get_db, get_gridfs_bucket
from config import settings

logger = logging.getLogger(__name__)


async def get_job(job_id: str) -> dict:
    """Get job from database"""
    db = get_db()
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def authorize_download(job: dict, user_id: int):
    """Check if user is authorized to download the file"""
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"File not ready. Current status: {job['status']}"
        )

    if "converted_file_id" not in job:
        raise HTTPException(
            status_code=500, detail="Converted file ID not found")


async def stream_file_from_gridfs(file_id: str):
    """Stream file from GridFS"""
    try:
        gridfs_bucket = get_gridfs_bucket()
        grid_out = await gridfs_bucket.open_download_stream(ObjectId(file_id))

        async def file_generator():
            while chunk := await grid_out.read(8192):
                yield chunk

        return file_generator()
    except Exception as e:
        logger.error(f"GridFS download error: {e}")
        raise HTTPException(status_code=500, detail="File retrieval failed")
