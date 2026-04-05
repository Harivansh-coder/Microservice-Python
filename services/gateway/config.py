# services/gateway/config.py
import os


class Settings:
    """Application configuration for gateway service"""
    AUTH_SERVICE_URL: str = os.getenv(
        "AUTH_SERVICE_URL", "http://localhost:8001")
    UPLOAD_SERVICE_URL: str = os.getenv(
        "UPLOAD_SERVICE_URL", "http://localhost:8002")
    DOWNLOAD_SERVICE_URL: str = os.getenv(
        "DOWNLOAD_SERVICE_URL", "http://localhost:8003")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    HTTP_CLIENT_TIMEOUT: float = float(
        os.getenv("HTTP_CLIENT_TIMEOUT", "30.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_UPLOAD_SIZE: int = int(
        os.getenv("MAX_UPLOAD_SIZE", str(500 * 1024 * 1024)))
    CONVERSION_SERVICE_URL: str = os.getenv(
        "CONVERSION_SERVICE_URL", "http://localhost:8004")


settings = Settings()
