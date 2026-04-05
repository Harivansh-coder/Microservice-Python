# services/notification/config.py
import os


class Settings:
    """Application configuration for notification service"""
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://localhost:5672/")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
