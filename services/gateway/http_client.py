# services/gateway/http_client.py
import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

http_client: Optional[httpx.AsyncClient] = None


async def initialize_http_client():
    """Initialize HTTP client with optimized settings for production"""
    global http_client
    http_client = httpx.AsyncClient(
        timeout=settings.HTTP_CLIENT_TIMEOUT,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20
        ),
        http2=True,
        verify=True
    )
    logger.info("HTTP client initialized with optimized settings")


async def close_http_client():
    """Close HTTP client"""
    global http_client
    if http_client:
        await http_client.aclose()
        logger.info("HTTP client closed")


def get_http_client() -> httpx.AsyncClient:
    """Get HTTP client instance"""
    if http_client is None:
        raise RuntimeError(
            "HTTP client not initialized. Call initialize_http_client() on startup.")
    return http_client
