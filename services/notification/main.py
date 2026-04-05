# services/notification/main.py
import logging
import asyncio
from fastapi import FastAPI
import aio_pika
from config import settings
from worker import NotificationWorker

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    description="Event-driven notification service"
)

# Global instances
worker: NotificationWorker = None
rabbitmq_connection = None
rabbitmq_channel = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global worker, rabbitmq_connection, rabbitmq_channel

    # RabbitMQ
    rabbitmq_connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    rabbitmq_channel = await rabbitmq_connection.channel()

    # Declare queue
    await rabbitmq_channel.declare_queue("conversion_events", durable=True)

    # Start worker
    worker = NotificationWorker(rabbitmq_channel)
    asyncio.create_task(worker.start())

    logger.info("Notification service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global rabbitmq_connection
    if worker:
        await worker.stop()
    if rabbitmq_connection:
        await rabbitmq_connection.close()
    logger.info("Notification service shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification",
        "worker_running": worker.running if worker else False,
        "notifications_sent": worker.notification_count if worker else 0,
        "dependencies": {
            "rabbitmq": "connected" if rabbitmq_connection else "disconnected"
        }
    }


@app.get("/stats")
async def get_stats():
    """Get notification statistics"""
    return {
        "total_notifications_sent": worker.notification_count if worker else 0,
        "worker_running": worker.running if worker else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
