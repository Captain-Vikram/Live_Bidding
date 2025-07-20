"""
Security middleware for the AgriTech Platform
Implements rate limiting, audit logging, and request validation
"""
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from typing import Dict, Optional
import asyncio
from collections import defaultdict
import json
from datetime import datetime
import redis
import os

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware to prevent abuse"""
    
    def __init__(self, app: FastAPI, calls: int = 1000, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        # Use Redis for distributed rate limiting
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Rate limiting using Redis")
        except Exception as e:
            logger.warning(f"Redis unavailable, falling back to memory: {e}")
            self.use_redis = False
            self.clients: Dict[str, list] = defaultdict(list)
            self.last_cleanup = time.time()
    
    def _cleanup_memory_cache(self):
        """Clean up old entries from memory cache periodically"""
        now = time.time()
        # Only cleanup every 60 seconds to avoid constant iteration
        if now - self.last_cleanup < 60:
            return
            
        self.last_cleanup = now
        clients_to_remove = []
        
        for client_ip, timestamps in self.clients.items():
            # Remove old timestamps
            self.clients[client_ip] = [
                timestamp for timestamp in timestamps
                if now - timestamp < self.period
            ]
            # If no recent requests, mark for removal
            if not self.clients[client_ip]:
                clients_to_remove.append(client_ip)
        
        # Remove inactive clients
        for client_ip in clients_to_remove:
            del self.clients[client_ip]
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        try:
            if self.use_redis:
                # Redis-based rate limiting
                key = f"rate_limit:{client_ip}"
                current = self.redis_client.get(key)
                
                if current is None:
                    # First request from this IP
                    self.redis_client.setex(key, self.period, 1)
                else:
                    current_count = int(current)
                    if current_count >= self.calls:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Rate limit exceeded",
                                "message": f"Maximum {self.calls} requests per {self.period} seconds",
                                "retry_after": self.redis_client.ttl(key)
                            }
                        )
                    # Increment counter
                    self.redis_client.incr(key)
            else:
                # Memory-based rate limiting with cleanup
                self._cleanup_memory_cache()
                
                # Clean old entries for this client
                self.clients[client_ip] = [
                    timestamp for timestamp in self.clients[client_ip]
                    if now - timestamp < self.period
                ]
                
                # Check rate limit
                if len(self.clients[client_ip]) >= self.calls:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {self.calls} requests per {self.period} seconds"
                        }
                    )
                
                # Record request
                self.clients[client_ip].append(now)
                
        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
        
        response = await call_next(request)
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for security tracking"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        request_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "headers": dict(request.headers)
        }
        
        # Process request
        response = await call_next(request)
        
        # Log response details
        process_time = time.time() - start_time
        response_data = {
            **request_data,
            "status_code": response.status_code,
            "process_time": round(process_time, 4)
        }
        
        # Log security-relevant events
        if response.status_code >= 400:
            logger.warning(f"Security event: {json.dumps(response_data)}")
        elif request.url.path.startswith("/api/v6/auth"):
            logger.info(f"Auth event: {json.dumps(response_data)}")
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Flexible CSP based on request path
        if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            # Allow Swagger UI and API docs to work
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https:"
        else:
            # Strict CSP for API endpoints
            response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        
        # Add CORS headers for allowed origins
        origin = request.headers.get("origin")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        allowed_origins = [frontend_url] + os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
        
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With"
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input to prevent injection attacks"""
    
    async def dispatch(self, request: Request, call_next):
        # Check for actual malicious patterns, not legitimate keywords
        suspicious_patterns = [
            # XSS patterns
            "<script", "javascript:", "onload=", "onerror=", "alert(", "document.cookie",
            # Path traversal
            "../", "..\\", "/etc/passwd", "/etc/shadow", "\\windows\\system32",
            # SQL injection context patterns (not just keywords)
            "'; DROP TABLE", "' OR '1'='1", "' OR 1=1", "UNION SELECT", "/*", "*/",
            # Command injection
            "; rm -rf", "| rm -rf", "&& rm -rf", "; del", "| del", "&& del"
        ]
        
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower() if request.url.query else ""
        
        # Check both path and query parameters
        full_request = f"{url_path} {query_string}"
        
        for pattern in suspicious_patterns:
            if pattern.lower() in full_request:
                logger.warning(f"Suspicious request blocked: {request.url} - Pattern: {pattern}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid request",
                        "message": "Request contains suspicious content"
                    }
                )
        
        response = await call_next(request)
        return response


def setup_security_middleware(app: FastAPI) -> FastAPI:
    """
    Setup all security middleware for the application
    """
    # Get configuration from environment
    rate_limit_calls = int(os.getenv("RATE_LIMIT_CALLS", "1000"))
    rate_limit_period = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=rate_limit_calls, period=rate_limit_period)
    
    logger.info(f"Security middleware configured: {rate_limit_calls} requests per {rate_limit_period}s")
    return app
