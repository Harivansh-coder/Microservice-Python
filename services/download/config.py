# services/download/config.py
import os


class Settings:
    """Application configuration for download service"""
    MONGO_URL: str = os.getenv(
        "MONGO_URL", "mongodb://localhost:27017/")
    MONGO_DB: str = os.getenv("MONGO_DB", "filestore")
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "change-me-replace-with-secure-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
