# services/gateway/main.py
import logging
import uuid
from fastapi import FastAPI, Request
from config import settings
from http_client import initialize_http_client, close_http_client
from cache import connect_to_redis, close_redis_connection
from routes import router

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    description="Unified API Gateway with JWT validation, rate limiting, and caching"
)

# Include routes
app.include_router(router)


# Middleware for correlation ID
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await initialize_http_client()
    await connect_to_redis(settings.REDIS_URL)
    logger.info("API Gateway started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_http_client()
    await close_redis_connection()
    logger.info("API Gateway shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from cache import redis_client
    return {
        "status": "healthy",
        "service": "api-gateway",
        "dependencies": {
            "redis": "connected" if redis_client else "disconnected"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
