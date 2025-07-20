"""
Security Middleware Integration
==============================

Integrates the security framework with FastAPI middleware for production deployment.
Implements rate limiting, audit logging, input sanitization, and security headers.
"""

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import logging
import json
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta
import redis
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security_enhanced import SecurityEnforcement, AuditLogger, InputSanitizer
from app.core.database import SessionLocal
from app.core.config import settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for the AgriTech platform
    """
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.security_enforcer = SecurityEnforcement()
        self.audit_logger = AuditLogger()
        self.input_sanitizer = InputSanitizer()
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through security layers
        """
        start_time = time.time()
        
        try:
            # 1. Apply security headers
            response = await self._apply_security_headers(request, call_next)
            
            # 2. Rate limiting check
            await self._check_rate_limits(request)
            
            # 3. Input sanitization
            await self._sanitize_request_input(request)
            
            # 4. Security audit logging
            await self._log_security_audit(request, response, start_time)
            
            return response
            
        except HTTPException as e:
            # Log security violations
            await self._log_security_violation(request, e)
            raise e
        except Exception as e:
            self.logger.error(f"Security middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal security error"
            )
    
    async def _apply_security_headers(self, request: Request, call_next: Callable) -> Response:
        """Apply security headers to response"""
        
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    async def _check_rate_limits(self, request: Request):
        """Check and enforce rate limits"""
        
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id_from_request(request)
        
        # Check IP-based rate limits
        ip_limit_key = f"rate_limit:ip:{client_ip}"
        ip_requests = self.redis_client.get(ip_limit_key)
        
        if ip_requests is None:
            # First request from this IP
            self.redis_client.setex(ip_limit_key, 60, 1)  # 1 minute window
        else:
            ip_requests = int(ip_requests)
            if ip_requests >= self.security_enforcer.config["RATE_LIMITS"]["PER_MINUTE"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded: Too many requests per minute"
                )
            self.redis_client.incr(ip_limit_key)
        
        # Check user-based rate limits if authenticated
        if user_id:
            user_limit_key = f"rate_limit:user:{user_id}"
            user_requests = self.redis_client.get(user_limit_key)
            
            if user_requests is None:
                self.redis_client.setex(user_limit_key, 3600, 1)  # 1 hour window
            else:
                user_requests = int(user_requests)
                if user_requests >= self.security_enforcer.config["RATE_LIMITS"]["PER_HOUR"]:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded: Too many requests per hour"
                    )
                self.redis_client.incr(user_limit_key)
    
    async def _sanitize_request_input(self, request: Request):
        """Sanitize request input data"""
        
        # Skip for certain content types and methods
        if request.method in ["GET", "DELETE"]:
            return
        
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return
        
        try:
            # Get request body
            body = await request.body()
            if not body:
                return
            
            # Parse JSON
            data = json.loads(body)
            
            # Sanitize string fields
            self._sanitize_dict_recursively(data)
            
            # Replace request body with sanitized data
            sanitized_body = json.dumps(data).encode()
            request._body = sanitized_body
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Invalid JSON or encoding - let the endpoint handle it
            pass
        except Exception as e:
            self.logger.warning(f"Input sanitization error: {str(e)}")
    
    def _sanitize_dict_recursively(self, data: Dict[str, Any]):
        """Recursively sanitize dictionary values"""
        
        for key, value in data.items():
            if isinstance(value, str):
                # Apply appropriate sanitization based on field name
                if any(field in key.lower() for field in ['email', 'mail']):
                    if not self.input_sanitizer.validate_email(value):
                        data[key] = self.input_sanitizer.sanitize_string(value)
                elif any(field in key.lower() for field in ['phone', 'mobile']):
                    if not self.input_sanitizer.validate_phone(value):
                        data[key] = self.input_sanitizer.sanitize_string(value)
                elif any(field in key.lower() for field in ['upi', 'payment']):
                    if not self.input_sanitizer.validate_upi_id(value):
                        data[key] = self.input_sanitizer.sanitize_string(value)
                else:
                    data[key] = self.input_sanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                self._sanitize_dict_recursively(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        value[i] = self.input_sanitizer.sanitize_string(item)
                    elif isinstance(item, dict):
                        self._sanitize_dict_recursively(item)
    
    async def _log_security_audit(self, request: Request, response: Response, start_time: float):
        """Log security audit information"""
        
        process_time = time.time() - start_time
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id_from_request(request)
        
        # Prepare audit data
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "user_id": user_id,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "request_size": len(await request.body()) if hasattr(request, '_body') else 0
        }
        
        # Log based on sensitivity
        if self._is_sensitive_endpoint(request.url.path):
            await self.audit_logger.log_data_access(
                user_id=user_id,
                resource_type="sensitive_endpoint",
                resource_id=request.url.path,
                action="access",
                metadata=audit_data
            )
        
        # Log authentication events
        if "/auth/" in request.url.path:
            event_type = "login_attempt" if "login" in request.url.path else "auth_action"
            success = 200 <= response.status_code < 300
            
            await self.audit_logger.log_authentication(
                user_id=user_id,
                event_type=event_type,
                success=success,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                metadata=audit_data
            )
    
    async def _log_security_violation(self, request: Request, exception: HTTPException):
        """Log security violations"""
        
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id_from_request(request)
        
        violation_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "user_id": user_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": exception.status_code,
            "error_detail": exception.detail,
            "user_agent": request.headers.get("user-agent", "")
        }
        
        # Determine violation type
        if exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            violation_type = "rate_limit_exceeded"
        elif exception.status_code == status.HTTP_401_UNAUTHORIZED:
            violation_type = "unauthorized_access"
        elif exception.status_code == status.HTTP_403_FORBIDDEN:
            violation_type = "forbidden_access"
        else:
            violation_type = "security_error"
        
        await self.audit_logger.log_security_violation(
            violation_type=violation_type,
            user_id=user_id,
            ip_address=client_ip,
            details=violation_data,
            severity="high" if exception.status_code in [401, 403] else "medium"
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        
        # Check for forwarded headers first (for proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client IP
        return request.client.host if request.client else "unknown"
    
    def _get_user_id_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated"""
        
        try:
            # Try to get from request state (set by auth middleware)
            if hasattr(request.state, "user_id"):
                return request.state.user_id
            
            # Try to extract from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would require JWT decoding - simplified for now
                # In practice, you'd decode the JWT and extract user_id
                return "authenticated_user"
            
            return None
        except Exception:
            return None
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint handles sensitive data"""
        
        sensitive_patterns = [
            "/auth/",
            "/admin/",
            "/kyc/",
            "/payment/",
            "/profile/",
            "/verify"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)


class AccountLockoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle account lockout after failed login attempts
    """
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.security_enforcer = SecurityEnforcement()
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check for account lockout on login attempts"""
        
        # Only apply to login endpoints
        if request.method == "POST" and "/auth/login" in str(request.url.path):
            client_ip = self._get_client_ip(request)
            
            # Check if IP is locked out
            lockout_key = f"lockout:{client_ip}"
            lockout_data = self.redis_client.get(lockout_key)
            
            if lockout_data:
                lockout_info = json.loads(lockout_data)
                lockout_until = datetime.fromisoformat(lockout_info["locked_until"])
                
                if datetime.utcnow() < lockout_until:
                    remaining_time = int((lockout_until - datetime.utcnow()).total_seconds())
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail=f"Account locked due to multiple failed attempts. Try again in {remaining_time} seconds."
                    )
                else:
                    # Lockout expired, remove it
                    self.redis_client.delete(lockout_key)
        
        response = await call_next(request)
        
        # Track failed login attempts
        if (request.method == "POST" and 
            "/auth/login" in str(request.url.path) and 
            response.status_code == 401):
            
            await self._track_failed_login(request)
        
        return response
    
    async def _track_failed_login(self, request: Request):
        """Track failed login attempts and implement lockout"""
        
        client_ip = self._get_client_ip(request)
        failed_attempts_key = f"failed_attempts:{client_ip}"
        
        # Get current failed attempts
        attempts = self.redis_client.get(failed_attempts_key)
        attempts = int(attempts) if attempts else 0
        attempts += 1
        
        # Update failed attempts counter
        self.redis_client.setex(failed_attempts_key, 1800, attempts)  # 30 minutes TTL
        
        # Check if lockout threshold reached
        max_attempts = self.security_enforcer.config["ACCOUNT_LOCKOUT"]["MAX_ATTEMPTS"]
        if attempts >= max_attempts:
            # Lock the account
            lockout_duration = self.security_enforcer.config["ACCOUNT_LOCKOUT"]["LOCKOUT_DURATION"]
            locked_until = datetime.utcnow() + timedelta(seconds=lockout_duration)
            
            lockout_data = {
                "locked_at": datetime.utcnow().isoformat(),
                "locked_until": locked_until.isoformat(),
                "attempts": attempts
            }
            
            lockout_key = f"lockout:{client_ip}"
            self.redis_client.setex(lockout_key, lockout_duration, json.dumps(lockout_data))
            
            # Clear failed attempts counter
            self.redis_client.delete(failed_attempts_key)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


def setup_security_middleware(app: FastAPI):
    """
    Configure all security middleware for the application
    """
    
    # CORS middleware (should be first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React frontend
            "http://localhost:8080",  # Vue frontend
            "http://localhost:4200",  # Angular frontend
            settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Account lockout middleware
    app.add_middleware(AccountLockoutMiddleware)
    
    # Trusted host middleware for production
    if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
        from fastapi.middleware.trustedhost import TrustedHostMiddleware
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                settings.DOMAIN_NAME if hasattr(settings, 'DOMAIN_NAME') else "localhost",
                "*.agritech.com"  # Allow subdomains in production
            ]
        )
    
    return app


# Security response headers for manual application
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}


async def apply_security_headers(response: Response) -> Response:
    """
    Manually apply security headers to a response
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response
