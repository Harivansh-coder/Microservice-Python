# services/conversion/main.py
import logging
from fastapi import FastAPI
import asyncio
import aio_pika
from db import connect_to_mongo, close_mongo_connection, get_db
from worker import ConversionWorker
from config import settings

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="File Conversion Service",
    version="1.0.0",
    description="MP4 to MP3 conversion worker service"
)

# Global worker instance
worker: ConversionWorker = None
rabbitmq_connection = None
rabbitmq_channel = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global worker, rabbitmq_connection, rabbitmq_channel

    # MongoDB
    await connect_to_mongo()

    # RabbitMQ
    rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    rabbitmq_channel = await rabbitmq_connection.channel()

    # Declare queues
    await rabbitmq_channel.declare_queue("conversion_jobs", durable=True)
    await rabbitmq_channel.declare_queue("conversion_events", durable=True)

    # Start worker
    worker = ConversionWorker(rabbitmq_channel)
    asyncio.create_task(worker.start())

    logger.info("Conversion service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global rabbitmq_connection
    if worker:
        await worker.stop()
    if rabbitmq_connection:
        await rabbitmq_connection.close()
    await close_mongo_connection()
    logger.info("Conversion service shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        await db.command("ping")
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"

    return {
        "status": "healthy",
        "service": "conversion",
        "worker_running": worker.running if worker else False,
        "dependencies": {
            "mongodb": mongo_status,
            "rabbitmq": "connected" if rabbitmq_connection else "disconnected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
