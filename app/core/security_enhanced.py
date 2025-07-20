"""
Phase 7: Security and Testing Implementation
===========================================

Security enhancements, comprehensive testing, and API documentation
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import secrets
import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Security Configuration
SECURITY_CONFIG = {
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_lowercase": True,
    "password_require_numbers": True,
    "password_require_special": True,
    "max_login_attempts": 5,
    "lockout_duration_minutes": 30,
    "jwt_expire_hours": 24,
    "refresh_token_expire_days": 30,
    "rate_limit_requests_per_minute": 60,
    "rate_limit_requests_per_hour": 1000
}


class SecurityEnforcement:
    """
    Advanced security enforcement system
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.failed_attempts = {}  # In production, use Redis
        self.rate_limits = {}  # In production, use Redis
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password meets security requirements
        """
        issues = []
        
        if len(password) < SECURITY_CONFIG["password_min_length"]:
            issues.append(f"Password must be at least {SECURITY_CONFIG['password_min_length']} characters")
        
        if SECURITY_CONFIG["password_require_uppercase"] and not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if SECURITY_CONFIG["password_require_lowercase"] and not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if SECURITY_CONFIG["password_require_numbers"] and not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if SECURITY_CONFIG["password_require_special"]:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                issues.append("Password must contain at least one special character")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength_score": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if any(c.isupper() for c in password):
            score += 15
        if any(c.islower() for c in password):
            score += 15
        if any(c.isdigit() for c in password):
            score += 15
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15
        
        return min(score, 100)
    
    def check_rate_limit(self, identifier: str, limit_type: str = "general") -> bool:
        """
        Check if request is within rate limits
        """
        now = datetime.utcnow()
        minute_key = f"{identifier}:{limit_type}:{now.strftime('%Y%m%d%H%M')}"
        hour_key = f"{identifier}:{limit_type}:{now.strftime('%Y%m%d%H')}"
        
        # Check minute limit
        minute_count = self.rate_limits.get(minute_key, 0)
        if minute_count >= SECURITY_CONFIG["rate_limit_requests_per_minute"]:
            return False
        
        # Check hour limit
        hour_count = self.rate_limits.get(hour_key, 0)
        if hour_count >= SECURITY_CONFIG["rate_limit_requests_per_hour"]:
            return False
        
        # Increment counters
        self.rate_limits[minute_key] = minute_count + 1
        self.rate_limits[hour_key] = hour_count + 1
        
        return True
    
    def record_failed_login(self, identifier: str) -> Dict[str, Any]:
        """
        Record failed login attempt and check if account should be locked
        """
        now = datetime.utcnow()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts (older than lockout duration)
        cutoff = now - timedelta(minutes=SECURITY_CONFIG["lockout_duration_minutes"])
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Add new failed attempt
        self.failed_attempts[identifier].append(now)
        
        attempts_count = len(self.failed_attempts[identifier])
        is_locked = attempts_count >= SECURITY_CONFIG["max_login_attempts"]
        
        return {
            "attempts_count": attempts_count,
            "max_attempts": SECURITY_CONFIG["max_login_attempts"],
            "is_locked": is_locked,
            "lockout_expires": now + timedelta(minutes=SECURITY_CONFIG["lockout_duration_minutes"]) if is_locked else None
        }
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed login attempts for successful login"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is currently locked"""
        if identifier not in self.failed_attempts:
            return False
        
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=SECURITY_CONFIG["lockout_duration_minutes"])
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        return len(recent_attempts) >= SECURITY_CONFIG["max_login_attempts"]
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data using SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
    """
    Security audit logging system
    """
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
        
        # In production, send to centralized logging system
        handler = logging.FileHandler("security_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_authentication_event(self, event_type: str, user_id: str = None, 
                                ip_address: str = None, user_agent: str = None,
                                success: bool = True, details: str = None):
        """Log authentication-related events"""
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"AUTH_EVENT: {log_data}")
    
    def log_data_access(self, user_id: str, resource: str, action: str,
                       ip_address: str = None, success: bool = True):
        """Log data access events"""
        log_data = {
            "event_type": "DATA_ACCESS",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"DATA_ACCESS: {log_data}")
    
    def log_security_violation(self, violation_type: str, user_id: str = None,
                             ip_address: str = None, details: str = None):
        """Log security violations"""
        log_data = {
            "event_type": "SECURITY_VIOLATION",
            "violation_type": violation_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.warning(f"SECURITY_VIOLATION: {log_data}")


class InputSanitizer:
    """
    Input sanitization and validation
    """
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not value:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "&", "\"", "'", "\x00"]
        for char in dangerous_chars:
            value = value.replace(char, "")
        
        # Limit length
        return value.strip()[:max_length]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Indian phone number format
        pattern = r'^\+91[6-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_upi_id(upi_id: str) -> bool:
        """Validate UPI ID format"""
        import re
        pattern = r'^[\w.-]+@[\w.-]+$'
        return bool(re.match(pattern, upi_id))


# Global security instances
security_enforcer = SecurityEnforcement()
audit_logger = AuditLogger()
input_sanitizer = InputSanitizer()


def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (for proxy/load balancer setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"


def get_user_agent(request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")
