# services/conversion/config.py
import os


class Settings:
    """Application configuration for conversion service"""
    MONGO_URL: str = os.getenv(
        "MONGO_URL", "mongodb://localhost:27017/")
    MONGO_DB: str = os.getenv("MONGO_DB", "filestore")
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://localhost:5672/")
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "2"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
