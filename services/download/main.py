# services/download/main.py
import logging
from fastapi import FastAPI
from db import connect_to_mongo, close_mongo_connection
from routes import router

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="File Download Service",
    version="1.0.0",
    description="MP3 file download service with MongoDB GridFS"
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await connect_to_mongo()
    logger.info("Download service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_mongo_connection()
    logger.info("Download service shutdown")

    response = {
        "job_id": job_id,
        "status": job["status"],
        "original_filename": job.get("original_filename"),
        "converted_filename": job.get("converted_filename"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at")
    }

    if job["status"] == "completed":
        try:
            file_info = await gridfs_bucket.find({"_id": ObjectId(job["converted_file_id"])}).to_list(1)
            if file_info:
                response["file_size"] = file_info[0].length
        except:
            pass

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
