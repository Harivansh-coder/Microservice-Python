# services/gateway/dependencies.py
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import logging
from config import settings
from http_client import get_http_client
from cache import get_cached_response, set_cached_response

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def check_rate_limit(redis_client, client_id: str) -> bool:
    """Check if client has exceeded rate limit"""
    key = f"rate_limit:{client_id}"
    current = await redis_client.get(key)

    if current is None:
        await redis_client.setex(key, settings.RATE_LIMIT_WINDOW, 1)
        return True

    if int(current) >= settings.RATE_LIMIT_REQUESTS:
        return False

    await redis_client.incr(key)
    return True


async def get_rate_limit_dependency(request: Request):
    """Rate limiting dependency"""
    from cache import redis_client
    if redis_client:
        client_id = request.client.host
        if not await check_rate_limit(redis_client, client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )


async def validate_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token with auth service"""
    try:
        http_client = get_http_client()
        response = await http_client.get(
            f"{settings.AUTH_SERVICE_URL}/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Auth service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
