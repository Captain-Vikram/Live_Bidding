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
from app.core.database import check_db_connection
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

# Enhanced CORS configuration to allow ANY localhost port
def is_localhost_origin(origin: str) -> bool:
    """Check if origin is from localhost or 127.0.0.1 with any port"""
    if not origin:
        return False
    
    import re
    # Pattern to match localhost:port or 127.0.0.1:port with any port number
    localhost_pattern = r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$'
    return bool(re.match(localhost_pattern, origin))

def get_dynamic_cors_origins():
    """Get CORS origins with localhost wildcard support"""
    # Start with configured origins
    origins = [str(origin) for origin in settings.CORS_ALLOWED_ORIGINS]
    
    # Add common localhost patterns for any port
    localhost_patterns = [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://localhost:*", 
        "https://127.0.0.1:*"
    ]
    
    # Add specific common development ports
    common_ports = [3000, 3001, 3002, 4000, 4200, 5000, 5173, 8000, 8080, 8081, 9000, 19000, 19001]
    for port in common_ports:
        origins.extend([
            f"http://localhost:{port}",
            f"http://127.0.0.1:{port}",
            f"https://localhost:{port}",
            f"https://127.0.0.1:{port}"
        ])
    
    # Add wildcard for any localhost origin in development
    if settings.DEBUG:
        origins.extend(["http://localhost:*", "http://127.0.0.1:*"])
    
    return origins

# Set all CORS enabled origins with localhost wildcard support
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_dynamic_cors_origins(),
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
        "x-api-key",
        "cache-control",
        "pragma"
    ],
    expose_headers=[
        "content-disposition",
        "content-type", 
        "content-length",
        "x-total-count",
        "x-page-count",
        "x-rate-limit-remaining"
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
)

# Handle OPTIONS requests explicitly for CORS preflight
@app.options("/")
async def options_root_handler(request: Request):
    """Handle CORS preflight requests for root - Allow ANY localhost port"""
    origin = request.headers.get("origin", "")
    
    # Allow any localhost or 127.0.0.1 origin with any port
    if is_localhost_origin(origin) or settings.DEBUG:
        allowed_origin = origin or "*"
    else:
        # Check against configured origins for production
        allowed_origins = [str(o) for o in settings.CORS_ALLOWED_ORIGINS]
        allowed_origin = origin if origin in allowed_origins else "null"
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with, guestuserid, x-api-key, cache-control, pragma",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
            "Vary": "Origin"
        }
    )

@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handle CORS preflight requests - Allow ANY localhost port"""
    origin = request.headers.get("origin", "")
    
    # Allow any localhost or 127.0.0.1 origin with any port
    if is_localhost_origin(origin) or settings.DEBUG:
        allowed_origin = origin or "*"
    else:
        # Check against configured origins for production
        allowed_origins = [str(o) for o in settings.CORS_ALLOWED_ORIGINS]
        allowed_origin = origin if origin in allowed_origins else "null"
    
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "accept, accept-encoding, authorization, content-type, dnt, origin, user-agent, x-csrftoken, x-requested-with, guestuserid, x-api-key, cache-control, pragma",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",  # 24 hours
            "Vary": "Origin"
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
    """Initialize connections on startup"""
    try:
        # Check database connection
        db_healthy = await check_db_connection()
        if db_healthy:
            logger.info("Database connected successfully")
        else:
            logger.error("Database connection failed during startup")
        
        # Initialize Redis connection
        await redis_manager.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Startup connection issues: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections on shutdown"""
    try:
        await redis_manager.disconnect()
        logger.info("Redis disconnected successfully")
    except Exception as e:
        logger.warning(f"Redis disconnection failed: {e}")


@app.get("/api/v6/healthcheck", name="Healthcheck", tags=["Healthcheck"])
async def healthcheck():
    return {"success": "pong!"}


@app.get("/api/v6/db-health", name="Database Health", tags=["Healthcheck"])
async def db_health():
    """Check Database connectivity"""
    try:
        is_healthy = await check_db_connection()
        return {
            "database_status": "healthy" if is_healthy else "unhealthy",
            "success": is_healthy
        }
    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
            "success": False
        }


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
