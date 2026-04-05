# services/conversion/worker.py
import logging
import os
import json
import asyncio
import subprocess
import tempfile
import aio_pika
from datetime import datetime
from bson import ObjectId
from db import get_db, get_gridfs_bucket
from config import settings

logger = logging.getLogger(__name__)

# Track processed jobs for idempotency
processed_jobs = set()


class ConversionWorker:
    def __init__(self, rabbitmq_channel: aio_pika.Channel):
        self.running = False
        self.rabbitmq_channel = rabbitmq_channel

    async def download_from_gridfs(self, file_id: str, temp_path: str):
        """Download file from GridFS to temp location"""
        gridfs_bucket = get_gridfs_bucket()
        grid_out = await gridfs_bucket.open_download_stream(ObjectId(file_id))

        with open(temp_path, 'wb') as f:
            while chunk := await grid_out.read(8192):
                f.write(chunk)

    async def upload_to_gridfs(self, file_path: str, metadata: dict) -> str:
        """Upload converted file to GridFS"""
        gridfs_bucket = get_gridfs_bucket()
        with open(file_path, 'rb') as f:
            file_id = await gridfs_bucket.upload_from_stream(
                metadata.get("filename", "audio.mp3"),
                f,
                metadata=metadata
            )
        return str(file_id)

    async def convert_mp4_to_mp3(self, input_path: str, output_path: str):
        """Convert MP4 to MP3 using FFmpeg (non-blocking subprocess)"""
        try:
            command = [
                'ffmpeg',
                '-i', input_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-ab', '192k',  # Audio bitrate
                '-ar', '44100',  # Sample rate
                '-y',  # Overwrite output
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=300  # 5 minute timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise Exception("Conversion timeout (5 minutes)")

            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")

            logger.info(f"Conversion successful: {output_path}")
            return True

        except asyncio.TimeoutError:
            raise Exception("Conversion timeout (5 minutes)")
        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")

    async def update_job_status(self, job_id: str, status: str, **kwargs):
        """Update job status in database"""
        db = get_db()
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        update_data.update(kwargs)

        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )

        logger.info(f"Job {job_id} status updated to: {status}")

    async def publish_completion_event(self, job_id: str, user_id: int, status: str, **kwargs):
        """Publish job completion event to notification queue"""
        event = {
            "job_id": job_id,
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        await self.rabbitmq_channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(event).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json"
            ),
            routing_key="conversion_events"
        )

        logger.info(f"Published completion event for job: {job_id}")

    async def process_job(self, message: aio_pika.IncomingMessage):
        """Process conversion job"""
        async with message.process():
            try:
                job_data = json.loads(message.body.decode())
                job_id = job_data["job_id"]
                file_id = job_data["file_id"]
                user_id = job_data["user_id"]
                filename = job_data["filename"]

                # Idempotency check
                if job_id in processed_jobs:
                    logger.warning(f"Job {job_id} already processed, skipping")
                    return

                logger.info(f"Processing job: {job_id}")

                # Update status to processing
                await self.update_job_status(job_id, "processing")

                # Create temp files
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as mp4_file, \
                        tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:

                    mp4_path = mp4_file.name
                    mp3_path = mp3_file.name

                try:
                    # Download MP4 from GridFS
                    logger.info(f"Downloading file {file_id}")
                    await self.download_from_gridfs(file_id, mp4_path)

                    # Convert to MP3
                    logger.info(f"Converting {filename}")
                    await self.convert_mp4_to_mp3(mp4_path, mp3_path)

                    # Upload MP3 to GridFS
                    mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                    metadata = {
                        "user_id": user_id,
                        "original_filename": filename,
                        "content_type": "audio/mpeg",
                        "job_id": job_id,
                        "converted_at": datetime.utcnow().isoformat()
                    }

                    converted_file_id = await self.upload_to_gridfs(mp3_path, metadata)

                    # Update job status to completed
                    await self.update_job_status(
                        job_id,
                        "completed",
                        converted_file_id=converted_file_id,
                        converted_filename=mp3_filename
                    )

                    # Publish completion event
                    await self.publish_completion_event(
                        job_id,
                        user_id,
                        "completed",
                        filename=mp3_filename
                    )

                    # Mark as processed
                    processed_jobs.add(job_id)

                    logger.info(f"Job {job_id} completed successfully")

                finally:
                    # Cleanup temp files
                    try:
                        os.unlink(mp4_path)
                        os.unlink(mp3_path)
                    except:
                        pass

            except Exception as e:
                logger.error(f"Job processing failed: {str(e)}")

                try:
                    await self.update_job_status(
                        job_id,
                        "failed",
                        error_message=str(e)
                    )

                    await self.publish_completion_event(
                        job_id,
                        user_id,
                        "failed",
                        error=str(e)
                    )
                except:
                    pass

    async def start(self):
        """Start consuming messages"""
        self.running = True
        queue = await self.rabbitmq_channel.declare_queue("conversion_jobs", durable=True)

        # Set prefetch count for concurrency control
        await self.rabbitmq_channel.set_qos(prefetch_count=settings.WORKER_CONCURRENCY)

        logger.info(
            f"Conversion worker started (concurrency: {settings.WORKER_CONCURRENCY})")

        await queue.consume(self.process_job)

    async def stop(self):
        """Stop worker"""
        self.running = False
