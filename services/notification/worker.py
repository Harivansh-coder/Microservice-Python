# services/notification/worker.py
import logging
import json
import asyncio
import aio_pika
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationWorker:
    def __init__(self, rabbitmq_channel: aio_pika.Channel):
        self.running = False
        self.notification_count = 0
        self.rabbitmq_channel = rabbitmq_channel

    async def send_notification(self, event_data: dict):
        """Send notification to user (structured logging for now)"""
        job_id = event_data.get("job_id")
        user_id = event_data.get("user_id")
        status = event_data.get("status")
        timestamp = event_data.get("timestamp")

        if status == "completed":
            filename = event_data.get("filename", "audio.mp3")
            message = f"Your file '{filename}' has been converted successfully!"
            log_level = logging.INFO
        elif status == "failed":
            error = event_data.get("error", "Unknown error")
            message = f"Conversion failed: {error}"
            log_level = logging.ERROR
        else:
            message = f"Job status updated to: {status}"
            log_level = logging.INFO

        # Structured log output
        logger.log(
            log_level,
            "NOTIFICATION",
            extra={
                "job_id": job_id,
                "user_id": user_id,
                "status": status,
                "message": message,
                "timestamp": timestamp
            }
        )

        # In production, this would:
        # - Send email via SMTP/SendGrid/SES
        # - Send push notification
        # - Send SMS
        # - Trigger webhook
        # - Store in user notification inbox

        self.notification_count += 1

        # Simulate notification service latency
        await asyncio.sleep(0.1)

    async def process_event(self, message: aio_pika.IncomingMessage):
        """Process conversion completion event"""
        async with message.process():
            try:
                event_data = json.loads(message.body.decode())
                logger.info(
                    f"Processing event for job: {event_data.get('job_id')}")

                await self.send_notification(event_data)

            except Exception as e:
                logger.error(
                    f"Event processing failed: {str(e)}", exc_info=True)

    async def start(self):
        """Start consuming messages"""
        self.running = True
        queue = await self.rabbitmq_channel.declare_queue("conversion_events", durable=True)

        logger.info("Notification worker started")

        await queue.consume(self.process_event)

    async def stop(self):
        """Stop worker"""
        self.running = False
        logger.info(
            f"Notification worker stopped. Total notifications sent: {self.notification_count}")
