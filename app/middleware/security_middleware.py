"""
Security middleware for the AgriTech Platform
Implements rate limiting, audit logging, and request validation
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from typing import Dict, Optional
import asyncio
from collections import defaultdict
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, app: FastAPI, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old entries
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
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input to prevent injection attacks"""
    
    async def dispatch(self, request: Request, call_next):
        # Check for suspicious patterns in URL
        suspicious_patterns = [
            "<script", "javascript:", "onload=", "onerror=",
            "SELECT", "DROP", "INSERT", "UPDATE", "DELETE",
            "../", "..\\", "/etc/passwd", "/etc/shadow"
        ]
        
        url_path = request.url.path.lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in url_path:
                logger.warning(f"Suspicious request blocked: {request.url}")
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
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(InputValidationMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RateLimitMiddleware, calls=1000, period=60)  # 1000 requests per minute
    
    logger.info("Security middleware configured successfully")
    return app
