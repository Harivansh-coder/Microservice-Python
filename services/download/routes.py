# services/download/routes.py
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
from utils import get_job, authorize_download, stream_file_from_gridfs

logger = logging.getLogger(__name__)

router = APIRouter(tags=["download"])


@router.get("/download/{job_id}")
async def download_file(
    job_id: str,
    x_user_id: int = Header(...),
    authorization: Optional[str] = Header(None)
):
    """Download converted MP3 file"""
    logger.info(f"Download request for job {job_id} by user {x_user_id}")

    # Get job
    job = await get_job(job_id)

    # Authorize
    await authorize_download(job, x_user_id)

    # Get file metadata
    from db import get_gridfs_bucket
    from bson import ObjectId

    try:
        gridfs_bucket = get_gridfs_bucket()
        file_info = await gridfs_bucket.find({"_id": ObjectId(job["converted_file_id"])}).to_list(1)
        if not file_info:
            raise HTTPException(
                status_code=404, detail="File not found in storage")

        filename = file_info[0].filename or "audio.mp3"
    except Exception as e:
        logger.error(f"File metadata error: {e}")
        filename = "audio.mp3"

    # Stream file
    file_stream = await stream_file_from_gridfs(job["converted_file_id"])

    return StreamingResponse(
        file_stream,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache"
        }
    )


@router.get("/info/{job_id}")
async def get_file_info(job_id: str, x_user_id: int = Header(...)):
    """Get file information without downloading"""
    job = await get_job(job_id)

    if job["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "filename": job.get("original_filename", "unknown"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at")
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from db import get_db
        db = get_db()
        await db.command("ping")
        mongo_status = "connected"
    except:
        mongo_status = "disconnected"

    return {
        "status": "healthy",
        "service": "download",
        "dependencies": {
            "mongodb": mongo_status
        }
    }
