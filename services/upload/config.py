# services/upload/config.py
import os


class Settings:
    """Application configuration for upload service"""
    MONGO_URL: str = os.getenv(
        "MONGO_URL", "mongodb://localhost:27017/")
    MONGO_DB: str = os.getenv("MONGO_DB", "filestore")
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://localhost:5672/")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
