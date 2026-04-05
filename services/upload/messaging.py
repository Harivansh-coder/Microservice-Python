# services/upload/messaging.py
import aio_pika
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

rabbitmq_connection: Optional[aio_pika.RobustConnection] = None
rabbitmq_channel: Optional[aio_pika.Channel] = None


async def connect_to_rabbitmq(rabbitmq_url: str):
    """Connect to RabbitMQ"""
    global rabbitmq_connection, rabbitmq_channel
    rabbitmq_connection = await aio_pika.connect_robust(rabbitmq_url)
    rabbitmq_channel = await rabbitmq_connection.channel()
    await rabbitmq_channel.declare_queue("conversion_jobs", durable=True)
    logger.info("Connected to RabbitMQ")


async def close_rabbitmq_connection():
    """Close RabbitMQ connection"""
    global rabbitmq_connection
    if rabbitmq_connection:
        await rabbitmq_connection.close()


async def publish_conversion_job(job_id: str, file_id: str, user_id: int, filename: str):
    """Publish job to conversion queue"""
    message = {
        "job_id": job_id,
        "file_id": file_id,
        "user_id": user_id,
        "filename": filename,
        "timestamp": datetime.utcnow().isoformat()
    }

    await rabbitmq_channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json"
        ),
        routing_key="conversion_jobs"
    )

    logger.info(f"Published conversion job: {job_id}")
