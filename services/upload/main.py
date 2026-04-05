# services/upload/main.py
import logging
from fastapi import FastAPI
from db import connect_to_mongo, close_mongo_connection, get_db
from messaging import connect_to_rabbitmq, close_rabbitmq_connection
from routes import router
from config import settings

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="File Upload Service",
    version="1.0.0",
    description="MP4 file upload and job management service"
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await connect_to_mongo()
    await connect_to_rabbitmq(settings.RABBITMQ_URL)
    logger.info("Upload service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_mongo_connection()
    await close_rabbitmq_connection()
    logger.info("Upload service shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        await db.command("ping")
        mongo_status = "connected"
    except:
        mongo_status = "disconnected"

    return {
        "status": "healthy",
        "service": "upload",
        "dependencies": {
            "mongodb": mongo_status,
            "rabbitmq": "connected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
