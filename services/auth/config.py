# services/auth/config.py
import os
from typing import Optional


class Settings:
    """Application configuration"""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost:5432/authdb")
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "change-me-replace-with-secure-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
