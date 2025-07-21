from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.requests import Request
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth, listings, general, seller, bidding, websocket, 
    price_tracking, mobile, notifications, commodities, 
    admin, auctioneer, recommendations
)
from app.api.routers import main_router
from app.common.exception_handlers import exc_handlers
from app.core.config import settings
from app.core.redis import redis_manager
from app.middleware.security_middleware import setup_security_middleware
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AgriTech Smart Bidding Platform with ML-powered recommendations and advanced security",
    openapi_url=f"/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    security=[{"BearerToken": [], "GuestUserID": []}],
    exception_handlers=exc_handlers,
)

# Setup security middleware with enhanced protection
app = setup_security_middleware(app)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=[
        "accept",
        "accept-encoding",
        "authorization",
        "content-type",
        "dnt",
        "origin",
        "user-agent",
        "x-csrftoken",
        "x-requested-with",
        "guestuserid",
        "access-control-allow-origin",
        "content-disposition",
    ],
    expose_headers=[
        "content-disposition",
        "content-type",
        "content-length",
    ],
)

# Handle OPTIONS requests explicitly for CORS preflight
@app.options("/")
async def options_root_handler(request: Request):
    """Handle CORS preflight requests for root"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with, guestuserid",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }
    )

@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight requests"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with, guestuserid",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }
    )

app.include_router(main_router, prefix="/api/v6")


@app.get("/", name="Root", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to AgriTech Platform API",
        "version": "6.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base": "/api/v6",
        "status": "running"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup"""
    try:
        await redis_manager.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Redis connection on shutdown"""
    try:
        await redis_manager.disconnect()
        logger.info("Redis disconnected successfully")
    except Exception as e:
        logger.warning(f"Redis disconnection failed: {e}")


@app.get("/api/v6/healthcheck", name="Healthcheck", tags=["Healthcheck"])
async def healthcheck():
    return {"success": "pong!"}


@app.get("/api/v6/redis-health", name="Redis Health", tags=["Healthcheck"])
async def redis_health():
    """Check Redis connectivity"""
    try:
        is_healthy = await redis_manager.is_healthy()
        return {
            "redis_status": "healthy" if is_healthy else "unhealthy",
            "success": is_healthy
        }
    except Exception as e:
        return {
            "redis_status": "error",
            "error": str(e),
            "success": False
        }
