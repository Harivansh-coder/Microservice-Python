# services/upload/routes.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Header, Request
from typing import Optional
import logging
from schemas import JobStatus, JobResponse
from utils import validate_mp4_file, store_file_in_gridfs, create_job
from messaging import publish_conversion_job
from db import get_db
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=JobResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    x_user_id: int = Header(...),
    x_username: str = Header(...),
    x_correlation_id: Optional[str] = Header(None)
):
    """Upload MP4 file and queue for conversion"""
    logger.info(
        f"Upload request from user {x_username} (ID: {x_user_id}), correlation: {x_correlation_id}")

    # Validate file type
    if not await validate_mp4_file(file):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only MP4 files are accepted.")

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        # Store file in GridFS
        from datetime import datetime
        metadata = {
            "user_id": x_user_id,
            "username": x_username,
            "content_type": file.content_type,
            "size": file_size,
            "correlation_id": x_correlation_id,
            "uploaded_at": datetime.utcnow().isoformat()
        }

        file_id = await store_file_in_gridfs(file, metadata)

        # Create job record
        job_data = {
            "user_id": x_user_id,
            "username": x_username,
            "original_filename": file.filename,
            "file_id": file_id,
            "status": "pending",
            "file_size": file_size,
            "correlation_id": x_correlation_id
        }

        job_id = await create_job(job_data)

        # Publish to RabbitMQ
        await publish_conversion_job(job_id, file_id, x_user_id, file.filename)

        logger.info(f"Job created: {job_id} for file: {file.filename}")

        return JobResponse(
            job_id=job_id,
            status="pending",
            message="File uploaded successfully. Conversion job queued."
        )

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, x_user_id: Optional[int] = Header(None)):
    """Get conversion job status"""
    db = get_db()
    job = await db.jobs.find_one({"job_id": job_id})

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Optional: Check if user owns this job
    if x_user_id and job["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return JobStatus(**job)
