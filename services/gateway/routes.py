# services/gateway/routes.py
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, StreamingResponse, Response
import httpx
import logging
import json
from config import settings
from http_client import get_http_client
from cache import get_cached_response, set_cached_response
from dependencies import validate_jwt, get_rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# Hop-by-hop headers to exclude
HOP_BY_HOP_HEADERS = {
    "connection", "transfer-encoding", "keep-alive",
    "proxy-authenticate", "proxy-authorization", "te",
    "trailer", "upgrade", "content-length"
}


def _filter_headers(headers: dict) -> dict:
    """Filter out hop-by-hop and sensitive headers"""
    return {
        k: v for k, v in headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }


def _is_json_response(content_type: str) -> bool:
    """Check if content type is JSON"""
    return content_type.split(";")[0].strip() == "application/json"


async def proxy_request(
    request: Request,
    target_url: str,
    cache_key: str = None,
    is_streaming: bool = False
):
    """Proxy request to backend service with improved error handling and caching"""
    # Validate target URL against allowed services (SSRF prevention)
    allowed_hosts = [
        settings.AUTH_SERVICE_URL,
        settings.UPLOAD_SERVICE_URL,
        settings.DOWNLOAD_SERVICE_URL,
        settings.CONVERSION_SERVICE_URL
    ]
    if not any(target_url.startswith(host) for host in allowed_hosts):
        logger.error(f"SSRF attempt detected: {target_url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target service"
        )

    # Check cache for GET requests
    if cache_key and request.method == "GET":
        cached = await get_cached_response(cache_key)
        if cached:
            logger.info(f"Cache hit: {cache_key}")
            return JSONResponse(content=cached)

    # Prepare headers
    headers = dict(request.headers)
    headers["X-Correlation-ID"] = request.state.correlation_id
    headers.pop("host", None)
    headers.pop("authorization", None)  # Don't forward auth to backend

    try:
        http_client = get_http_client()
        body = await request.body()

        # Non-streaming proxy
        if not is_streaming:
            response = await http_client.request(
                method=request.method,
                url=target_url,
                headers=_filter_headers(headers),
                content=body,
                params=request.query_params,
                timeout=settings.HTTP_CLIENT_TIMEOUT
            )

            # Cache successful GET responses
            if cache_key and request.method == "GET" and response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if _is_json_response(content_type):
                    try:
                        data = response.json()
                        await set_cached_response(cache_key, data, ttl=300)
                    except (ValueError, json.JSONDecodeError) as e:
                        logger.warning(
                            f"Failed to cache response for {cache_key}: {e}")

            # Return JSON or raw response appropriately
            content_type = response.headers.get("content-type", "")
            if _is_json_response(content_type):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=_filter_headers(dict(response.headers))
                )
            else:
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    media_type=content_type,
                    headers=_filter_headers(dict(response.headers))
                )

    except httpx.RequestError as e:
        logger.error(f"Proxy request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upstream service unavailable",
            headers={"X-Correlation-ID": request.state.correlation_id}
        )


# Auth endpoints (public)
@router.post("/auth/register", dependencies=[Depends(get_rate_limit_dependency)])
async def register(request: Request):
    """Register new user"""
    return await proxy_request(request, f"{settings.AUTH_SERVICE_URL}/register")


@router.post("/auth/login", dependencies=[Depends(get_rate_limit_dependency)])
async def login(request: Request):
    """User login"""
    return await proxy_request(request, f"{settings.AUTH_SERVICE_URL}/login")


@router.post("/auth/refresh", dependencies=[Depends(get_rate_limit_dependency)])
async def refresh_token(request: Request):
    """Refresh access token using refresh token"""
    return await proxy_request(request, f"{settings.AUTH_SERVICE_URL}/refresh")


@router.post("/auth/logout", dependencies=[Depends(validate_jwt), Depends(get_rate_limit_dependency)])
async def logout(request: Request):
    """User logout (requires JWT)"""
    return await proxy_request(request, f"{settings.AUTH_SERVICE_URL}/logout")


@router.get("/auth/me", dependencies=[Depends(validate_jwt), Depends(get_rate_limit_dependency)])
async def get_user_info(request: Request):
    """Get current user info"""
    return await proxy_request(request, f"{settings.AUTH_SERVICE_URL}/me")


# Upload endpoints (protected)
@router.post("/upload", dependencies=[Depends(validate_jwt), Depends(get_rate_limit_dependency)])
async def upload_file(request: Request, user_data: dict = Depends(validate_jwt)):
    """Upload MP4 file for conversion"""
    target_url = f"{settings.UPLOAD_SERVICE_URL}/upload"

    headers = dict(request.headers)
    headers["X-Correlation-ID"] = request.state.correlation_id
    headers["X-User-ID"] = str(user_data["user_id"])
    headers["X-Username"] = user_data["username"]
    headers.pop("host", None)

    try:
        http_client = get_http_client()
        body = await request.body()

        # Validate request size
        if len(body) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
            )

        response = await http_client.post(
            url=target_url,
            headers=_filter_headers(headers),
            content=body,
            timeout=settings.HTTP_CLIENT_TIMEOUT
        )

        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers={"X-Correlation-ID": request.state.correlation_id}
        )
    except httpx.RequestError as e:
        logger.error(f"Upload request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upload service unavailable",
            headers={"X-Correlation-ID": request.state.correlation_id}
        )


@router.get("/jobs/{job_id}", dependencies=[Depends(validate_jwt), Depends(get_rate_limit_dependency)])
async def get_job_status(request: Request, job_id: str):
    """Get conversion job status"""
    cache_key = f"job_status:{job_id}"
    return await proxy_request(
        request,
        f"{settings.UPLOAD_SERVICE_URL}/jobs/{job_id}",
        cache_key=cache_key
    )


# Download endpoints (protected)
@router.get("/download/{job_id}", dependencies=[Depends(validate_jwt), Depends(get_rate_limit_dependency)])
async def download_file(request: Request, job_id: str, user_data: dict = Depends(validate_jwt)):
    """Download converted MP3 file (streaming)"""
    target_url = f"{settings.DOWNLOAD_SERVICE_URL}/download/{job_id}"

    headers = dict(request.headers)
    headers["X-Correlation-ID"] = request.state.correlation_id
    headers["X-User-ID"] = str(user_data["user_id"])
    headers.pop("host", None)

    try:
        http_client = get_http_client()
        async with http_client.stream(
            "GET",
            target_url,
            headers=_filter_headers(headers),
            timeout=settings.HTTP_CLIENT_TIMEOUT
        ) as response:
            if response.status_code != 200:
                error_data = await response.aread()
                return JSONResponse(
                    content={"detail": error_data.decode()},
                    status_code=response.status_code,
                    headers={"X-Correlation-ID": request.state.correlation_id}
                )

            async def stream_generator():
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk

            return StreamingResponse(
                stream_generator(),
                media_type=response.headers.get("content-type", "audio/mpeg"),
                headers={
                    "Content-Disposition": response.headers.get(
                        "content-disposition",
                        "attachment; filename=audio.mp3"
                    ),
                    "X-Correlation-ID": request.state.correlation_id,
                    **_filter_headers(dict(response.headers))
                }
            )
    except httpx.RequestError as e:
        logger.error(f"Download request failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Download service unavailable",
            headers={"X-Correlation-ID": request.state.correlation_id}
        )
